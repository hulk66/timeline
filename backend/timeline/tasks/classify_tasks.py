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
import tempfile

import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image
from pymysql.err import OperationalError
from timeline.domain import Photo, Thing
from timeline.extensions import celery, db
from timeline.util.path_util import get_full_path

logger = logging.getLogger(__name__)
CLASSIFICATION_SCORE = 0.5
object_detector = None
logger = logging.getLogger(__name__)


def init_classify_services(path_to_model):

    global object_detector
    logger.debug("Initialize Thing Detection Services, might need to download a model")
    # module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
    # module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
    # module_handle = "models/thing/ssd"
    object_detector = hub.load(path_to_model).signatures['default']
    logger.debug("Initialize Thing Detection Services done")

def run_detector(image_path):

    # logger.debug("run_object_detector for %s", image_path)
    jpg_file = load_and_resize_image(image_path)
    tensor = image_to_tensor(jpg_file)
    #if object_detector is None:
    #    init_classify_services("models/thing/ssd")
    detection_result = object_detector(tensor)

    r = {key: value.numpy() for key, value in detection_result.items()}
    entities = r["detection_class_entities"]
    scores = r["detection_scores"]
    classes = r['detection_class_names']

    result = {}
    for i in range(100):
        # entity = entities[i]
        score = scores[i]
        clazz = classes[i].decode()
        if score > CLASSIFICATION_SCORE:
            result[clazz] = score
        else:
            break
    os.remove(jpg_file)
    return result

@celery.task(autoretry_for=(OperationalError,), name="Object Detection", ignore_result=True)
def analyze_photo(photo_id):
    photo = Photo.query.get(photo_id)
    logger.debug("Analyze Photo %s", photo.path)

    if not photo:
        logger.error("Something is wrong. Photo with id %i not found")
        return

    path = get_full_path(photo.path)
    if not os.path.exists(path):
        logger.warning("Can't open file %s for object detection. May have been removed?", path)
        return

    detected_objects = run_detector(path)
    for clazz in detected_objects:
        thing = Thing.query.get(clazz)
        photo.things.append(thing)
    # photo.status = "analyzed"
    db.session.commit()
    logger.debug("Analyze Photo %s ok. Found %i classes", photo.path, len(detected_objects))

def load_and_resize_image(fname, max_dim=1280):
    _, filename = tempfile.mkstemp(suffix=".jpg")
    pil_image = Image.open(fname)
    pil_image.thumbnail((max_dim, max_dim))
    pil_image_rgb = pil_image.convert("RGB")
    pil_image_rgb.save(filename, format="JPEG", quality=90)
    return filename

def load_img(path):
    img = tf.io.read_file(path)
    img = tf.image.decode_jpeg(img, channels=3)
    return img

def image_to_tensor(path):
    img = load_img(path)
    converted_img = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
    return converted_img
