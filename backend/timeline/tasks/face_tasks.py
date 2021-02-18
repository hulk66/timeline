'''
Copyright (C) 2021 Tobias Himstedt


This file is part of Timeline.

Timeline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Timeline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

import logging
import os
from datetime import datetime

import mtcnn
import numpy
from keras_vggface import VGGFace
from keras_vggface.utils import preprocess_input
from PIL import Image
from pymysql.err import InternalError
from sklearn.preprocessing import normalize
from timeline.domain import Face, Photo
from timeline.extensions import celery, db
from timeline.util.image_ops import read_transpose_scale_image_as_array
from timeline.util.path_util import get_full_path
from timeline.tasks.match_tasks import match_unknown_face
from timeline.util.path_util import get_preview_path

logger = logging.getLogger(__name__)

MIN_DIMENSION_SIZE = 50
face_detector = None
face_identifier = None


def init_face_services():
    global face_detector
    global face_identifier
    logger.debug(
        "Initialize Face Detection Services. Potentially downloading a model, might need a couple of seconds")

    face_detector = mtcnn.MTCNN()
    face_identifier = VGGFace(model='resnet50',
                              include_top=False,
                              input_shape=(224, 224, 3),
                              pooling='avg')
    logger.debug("Face Detection Services initialized")


def _get_face_embeddings(faces):
    #tb._SYMBOLIC_SCOPE.value = True

    samples = numpy.asarray(faces, 'float32')
    samples = preprocess_input(samples, version=2)
    return face_identifier.predict(samples)


def _find_faces_in_image(image):
    face_pos = face_detector.detect_faces(image)
    required_size = (224, 224)

    image_list = []
    face_result = []
    for face in face_pos:
        x1, y1, width, height = face['box']

        x2, y2 = x1 + width, y1 + height
        # add a little extra space

        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        if x2 > image.shape[1]:
            x2 = image.shape[1]
        if y2 > image.shape[0]:
            y2 = image.shape[0]

        if x2 - x1 > MIN_DIMENSION_SIZE and y2 - y1 > MIN_DIMENSION_SIZE:
            # extract the face only if bigger than a certain threshold
            face_boundary = image[y1:y2, x1:x2]
            # resize pixels to the model size
            face_image = Image.fromarray(face_boundary)
            face_image = face_image.resize(required_size)
            face_as_array = numpy.asarray(face_image)
            image_list.append(face_as_array)
            face_result.append(face)
    return face_result, image_list


@celery.task(name="Face Detection", autoretry_for=(InternalError,), ignore_result=True)
def find_faces(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        logger.error(
            "Something is wrong. Can't find photo with ID %i", photo_id)
        return

    logger.debug("Find Faces in %s", photo.path)
    path = get_full_path(photo.path)
    if not os.path.exists(path):
        logger.warning(
            "File for face detection does not exist. Maybe it has removed meanwhile? %s", path)
        return
    image, scale_factor = read_transpose_scale_image_as_array(path, 2000)
    face_positions, faces = _find_faces_in_image(image)
    num_faces = 0
    result = []
    if len(face_positions) > 0:
        # self.logger.debug("Get scores %s", path)
        model_scores = _get_face_embeddings(faces)
        scores_nomalized = normalize(model_scores)
        # self.logger.debug("... ok %s", path)

        i = 0
        for fbox in face_positions:
            confidence = fbox['confidence']
            if confidence > 0.95:
                num_faces += 1
                face = Face()
                face.created = datetime.today()
                face.ignore = False
                face.already_clustered = False
                x, y, w, h = fbox['box']
                face.x, face.y, face.w, face.h = x * scale_factor, y * \
                    scale_factor, w * scale_factor, h * scale_factor
                face.encoding = scores_nomalized[i]
                result.append(face)
            i += 1
        photo.faces = result
        db.session.commit()
        for face in photo.faces:
            # for all found faces we will check if we can match is already to some known face
            match_unknown_face.apply_async((face.id,), queue="match")


def save_preview(id, image):
    preview_path = get_preview_path(str(id) + ".png", "faces")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path)
