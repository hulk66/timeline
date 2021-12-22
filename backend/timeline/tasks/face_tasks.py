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

import numpy
from keras_vggface import VGGFace
from keras_vggface.utils import preprocess_input
from PIL import Image
from pymysql.err import InternalError
from sklearn.preprocessing import normalize
from timeline.domain import Face, Asset
from timeline.extensions import celery, db
from timeline.util.image_ops import read_transpose_scale_image_as_array
from timeline.util.path_util import get_full_path
from timeline.tasks.match_tasks import match_unknown_face, match_ignored_faces
from timeline.util.path_util import get_preview_path
import face_recognition
from timeline.facial.expression import FacialExpression, AgeGender

logger = logging.getLogger(__name__) 
MIN_DIMENSION_SIZE = 50


def init_face_age_gender():
    global face_expression
    #global age_gender
    face_expression = FacialExpression()
    logger.debug("Expression Detector initialized")                              
    #age_gender = AgeGender()
    #logger.debug("Age/Gender Detector initialized")


def init_vgg_face():
    global face_identifier
    logger.debug("Initialize VGGFace, might need a couple of seconds")

    # face_detector = mtcnn.MTCNN()
    face_identifier = VGGFace(model='resnet50',
                              include_top=False,
                              input_shape=(224, 224, 3),
                              pooling='avg')
    logger.debug("VGGFace initialized")                              


def _get_face_embeddings(faces):
    samples = numpy.asarray(faces, 'float32')
    samples = preprocess_input(samples, version=2)
    return face_identifier.predict(samples)

def _find_faces_in_image2(image):
    required_size = (224, 224)
    image_list = []
    face_result = []

    face_locations = face_recognition.face_locations(image)    
    
    for face_location in face_locations:
        y1, x2, y2, x1 = face_location

        if x2 - x1 > MIN_DIMENSION_SIZE and y2 - y1 > MIN_DIMENSION_SIZE:
            # extract the face only if bigger than a certain threshold
            face_boundary = image[y1:y2, x1:x2]
            # resize pixels to the model size
            face_image = Image.fromarray(face_boundary)
            face_image = face_image.resize(required_size)
            face_as_array = numpy.asarray(face_image)
            image_list.append(face_as_array)
            face_result.append(face_location) 
    return face_result, image_list

@celery.task(name="Face Detection", autoretry_for=(InternalError,), ignore_result=True)
def find_faces2(asset_id, call_match_tasks = True):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.error(
            "Something is wrong. Can't find asset with ID %i", asset_id)
        return

    logger.debug("Find Faces in %s", asset.path)
    path = get_full_path(asset.path)
    if not os.path.exists(path):
        logger.warning(
            "File for face detection does not exist. Maybe it has removed meanwhile? %s", path)
        return
    image, scale_factor = read_transpose_scale_image_as_array(path, 2000)
    face_positions, faces = _find_faces_in_image2(image)
    num_faces = 0
    result = []
    if len(face_positions) > 0:

        logger.debug("Get Feature Vector for Face")
        model_scores = _get_face_embeddings(faces)
        scores_nomalized = normalize(model_scores)

        i = 0
        for face_locations in face_positions:
            num_faces += 1
            face = Face()
            face.created = datetime.today()
            face.ignore = False
            face.already_clustered = False

            y1, x2, y2, x1 = face_locations
            face.x, face.y, face.w, face.h = int(x1 * scale_factor), int(y1 * \
                scale_factor), int((x2-x1) * scale_factor), int((y2-y1) * scale_factor)
            face.encoding = scores_nomalized[i]
            result.append(face)
            i += 1
        asset.faces = result
        db.session.commit()
        if call_match_tasks:
            for face in asset.faces:

                # for all found faces we will check if we can match is already to some known face
                match_unknown_face.apply_async((face.id,), queue="analyze")
                # and if it is close to an already ignored face, then also ignore it
                match_ignored_faces.apply_async((face.id,), queue="analyze")
                # and finally find out the emotion of a face for later grouping
                detect_facial_expression.apply_async((face.id,), queue="analyze")
                #detect_age.apply_async((face.id,), queue="analyze")
                #detect_gender.apply_async((face.id,), queue="analyze")
                

    logger.debug("Found %d faces in %s", num_faces, asset.path)

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


def _get_cropped_face(face, margin=0.3):
    asset = face.asset
    path = get_full_path(asset.path)
    image, scale_factor = read_transpose_scale_image_as_array(path)
    margin_w = face.w * margin
    margin_h = face.h * margin

    x1 = face.x
    x2 = face.x + face.w
    y1 = face.y
    y2 = face.y + face.h

    #y1 = int(face.y - margin_h)
    #y1 = y1 if y1 > 0 else 0
    #y2 = int(y1 + face.h + 2*margin_h)
    #y2 = y2 if y2 < image.shape[1] else image.shape[1]

    #x1 = int(face.x - margin_w)
    #x1 = x1 if x1 > 0 else 0
    #x2 = int(x1 + face.w + 2*margin_w)
    #x2 = x2 if x2 < image.shape[0] else image.shape[0]
    face_array = image[y1:y2, x1:x2]


    # face_array = image[face.y - margin_h:face.y + face.h, face.x:face.x+face.w]
    face_image = Image.fromarray(face_array)
    return face_image


@celery.task(name="Detect Face Gender", autoretry_for=(InternalError,), ignore_result=True)
def detect_gender(face_id):
    logger.debug("Detect Face Gender for Face %i", face_id)
    face = Face.query.get(face_id)
    if not face:
        logger.error(
            "Something is wrong. Can't find face with ID %i", face_id)
        return
    face_image = _get_cropped_face(face)
    face.predicted_gender = age_gender.predict_gender(face_image)
    db.session.commit()

@celery.task(name="Detect Face Age", autoretry_for=(InternalError,), ignore_result=True)
def detect_age(face_id):
    logger.debug("Detect Face Age for Face %i", face_id)
    face = Face.query.get(face_id)
    if not face:
        logger.error(
            "Something is wrong. Can't find face with ID %i", face_id)
        return
    face_image = _get_cropped_face(face)
    age = age_gender.predict_age(face_image)
    face.predicted_age = int(age)
    db.session.commit()

@celery.task(name="Detect Face Expression", autoretry_for=(InternalError,), ignore_result=True)
def detect_facial_expression(face_id):
    logger.debug("Detect Face Expression for Face %i", face_id)
    face = Face.query.get(face_id)
    if not face:
        logger.error(
            "Something is wrong. Can't find face with ID %i", face_id)
        return

    face_image = _get_cropped_face(face)
    face.emotion, face.emotion_confidence = face_expression.predict(face_image)
    db.session.commit()

@celery.task(name="Face Detection old", autoretry_for=(InternalError,), ignore_result=True)
def find_faces(asset_id, call_match_tasks):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.error(
            "Something is wrong. Can't find asset with ID %i", asset_id)
        return

    logger.debug("Find Faces in %s", asset.path)
    path = get_full_path(asset.path)
    if not os.path.exists(path):
        logger.warning(
            "File for face detection does not exist. Maybe it has removed meanwhile? %s", path)
        return
    image, scale_factor = read_transpose_scale_image_as_array(path, 2000)
    face_positions, faces = _find_faces_in_image(image)
    num_faces = 0
    result = []
    if len(face_positions) > 0:
        logger.debug("Get scores %s", path)
        model_scores = _get_face_embeddings(faces)
        scores_nomalized = normalize(model_scores)
        logger.debug("... ok %s", path)

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
        asset.faces = result
        logger.debug("Found %d faces in %s", num_faces, asset.path)
        db.session.commit()
        if call_match_tasks:
            for face in asset.faces:
                # for all found faces we will check if we can match is already to some known face
                match_unknown_face.apply_async((face.id,), queue="analyze")
                # and if it is close to an already ignored face, then also ignore it
                match_ignored_faces.apply_async((face.id,), queue="analyze")
                # and finally find out the emotion of a face for later grouping
                detect_facial_expression.apply_async((face.id,), queue="analyze")


def save_preview(id, image):
    preview_path = get_preview_path(str(id) + ".png", "faces")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path)
