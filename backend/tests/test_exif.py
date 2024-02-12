from timeline.domain import Asset, Status, Face
import unittest
from timeline.app import create_app
from timeline.extensions import db
from timeline.tasks.crud_tasks import create_asset
from timeline.api.views import crop_face
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import get_full_path

TEST_FILE="tests/gps.jpg"

class TestExif(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()


    def test_exif(self):
        with self.app.app_context():
            create_asset(TEST_FILE)
            photo = Asset.query.first()
            assert photo
            assert photo.exif
            assert any(exif.key == "FNumber" for exif in photo.exif)
            assert any(exif.key == "Make" for exif in photo.exif)

    def test_exif_old_photo(self):
        with self.app.app_context():
            create_asset(TEST_FILE)
            photo = Asset.query.first()
            assert photo
            assert photo.exif
            assert any(exif.key == "Make" for exif in photo.exif)
            assert any(exif.key == "Make" for exif in photo.exif)

    def test_gps(self):
        with self.app.app_context():
            create_asset(TEST_FILE)
            photo = Asset.query.first()
            assert photo
            assert photo.gps
            assert photo.gps.latitude
            assert photo.gps.longitude
