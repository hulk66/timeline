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

import numpy as np
import tensorflow as tf
from brisque.brisque import BRISQUE
from idealo.handlers.model_builder import Nima
from idealo.utils.utils import calc_mean_score
from tensorflow.keras.applications.mobilenet import preprocess_input
from timeline.domain import Photo
from timeline.extensions import celery, db
from timeline.util.path_util import get_full_path

logger = logging.getLogger(__name__)


class ImageQualifier:

    def __init__(self):
        self.nima_aesthetics = Nima("MobileNet", weights=None)
        self.nima_aesthetics.build()
        self.nima_aesthetics.nima_model.load_weights(
            "model/weights_mobilenet_aesthetic_0.07.hdf5")

        self.nima_technical = Nima("MobileNet", weights=None)
        self.nima_technical.build()
        self.nima_technical.nima_model.load_weights(
            "model/weights_mobilenet_technical_0.11.hdf5")
        self.brisque = BRISQUE()

    def _preprocess(self, img):
        preprocessed_img = tf.keras.preprocessing.image.load_img(
            img, target_size=(224, 224))
        img_as_array = np.asarray(preprocessed_img)
        expended_img_arrary = np.expand_dims(img_as_array, axis=0)
        preprocessed = preprocess_input(expended_img_arrary)
        return preprocessed

    def predict(self, photo_id):
        photo = Photo.query.get(photo_id)
        logger.debug("Image Aesthetics qualification for %s", photo.path)
        path = get_full_path(photo.path)

        preprocessed = self._preprocess(path)
        prediction_aesthetic = self.nima_aesthetics.nima_model(preprocessed)
        photo.score_aesthetic = calc_mean_score(prediction_aesthetic)

        prediction_technical = self.nima_technical.nima_model(preprocessed)
        photo.score_technical = calc_mean_score(prediction_technical)
        logger.debug("Image Aesthetics qualification for %s done (%f, %f)",
                     photo.path, photo.score_aesthetic, photo.score_technical)

        db.session.commit()

    def calculate_brisque(self, photo_id):
        photo = Photo.query.get(photo_id)
        logger.debug("Brisque score for %s", photo.path)
        path = get_full_path(photo.path)
        photo.score_brisque = self.brisque.get_score(path)
        db.session.commit()
        logger.debug("Brisque score for %s: %f",
                     photo.path, photo.score_brisque)


qualifier = ImageQualifier()


@celery.task(ignore_result=True)
def predict_quality(photo_id):
    qualifier.predict(photo_id)


@celery.task(ignore_result=True)
def brisque_score(photo_id):
    qualifier.calculate_brisque(photo_id)
