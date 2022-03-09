
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
from timeline.tasks.find_events_tasks import find_events
from timeline.app import create_app
from timeline.extensions import db
from timeline.domain import Asset, Status
import os
import shutil
 
class TestEvents(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")


    def test_events(self) -> None:
        find_events()

if __name__ == '__main__':
    unittest.main()
