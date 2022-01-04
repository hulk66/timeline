import unittest
import tensorflow as tf
import numpy as np


from timeline.app import create_app
from idealo.handlers.model_builder import Nima
from idealo.utils.utils import calc_mean_score
from tensorflow.keras.applications.mobilenet import preprocess_input
from timeline.tasks.iq_tasks import ImageQualifier
from timeline.extensions import db
from timeline.domain import Asset, Status, Face
from timeline.tasks.crud_tasks import create_asset

from tensorflow import keras
from tensorflow.keras.layers import GlobalAveragePooling2D

class TestImageAssessment(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.test")
        with self.app.app_context():
            db.session.add(Status())
            db.session.commit()
 
    def test_quali(self):
        nima = Nima("MobileNet", weights=None)
        nima.build()
        nima.nima_model.load_weights("models/iq/weights_mobilenet_aesthetic_0.07.hdf5")

        preprocessed_img = tf.keras.preprocessing.image.load_img("tests/gps.jpg", target_size=(224, 224))
        img_as_array = np.asarray(preprocessed_img)
        x = np.expand_dims(img_as_array, axis=0)
        v = preprocess_input(x)
        pred = nima.nima_model(v)
        score2 = calc_mean_score(pred)

        assert nima
        assert score2

    def test_iq(self):
        qualifier = ImageQualifier()

        with self.app.app_context():
            id = create_asset("tests/gps.jpg")
            qualifier.predict(id)    
            asset = Asset.query.get(id)

            assert asset.score_aesthetic != 0.0            
            assert asset.score_technical != 0.0