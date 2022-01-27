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

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")

    # make sure test_cache1 was running before
    def test_cache_survice(self):
        with self.app.app_context():
            result = cache.get("faces2")
            assert result
            
if __name__ == '__main__':
    unittest.main()
