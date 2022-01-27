import context
import io
import unittest
from PIL import Image
from pillow_heif import register_heif_opener
from timeline.tasks.crud_tasks import delete_asset
from timeline.tasks.geo_tasks import resolve_address
from timeline.tasks.crud_tasks import create_preview
from timeline.tasks.crud_tasks import create_asset
from timeline.util.gps import (get_geotagging, get_gps_data,
                               get_labeled_exif, get_lat_lon)
from timeline.tasks.geo_tasks import geolocator
from timeline.app import create_app
from timeline.extensions import db, cache
from timeline.domain import Asset, Status, Face, Person
import os
import shutil
import time

class TestHeif(unittest.TestCase):

    # make sure to have Redis running (docker-compose up redis) before starting the test
    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")

    def test_set_data(self):
        with self.app.app_context():
            faces = Face.query.join(Person).filter(Person.confirmed == True).with_entities(Face.id, Face.encoding).limit(5000).all()
            cache.set("faces", faces, timeout=5)
            cache.set("faces2", faces)

            cache_result = cache.get("faces")
            assert len(cache_result) == len(faces)
            time.sleep(5)
            cache_result = cache.get("faces")
            assert cache_result is None

            
if __name__ == '__main__':
    unittest.main()
