
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
from timeline.extensions import db
from timeline.domain import Asset, Status
import os
import shutil

class TestHeif(unittest.TestCase):

    def setUp(self):
        register_heif_opener()      
        self.app = create_app(testing=True, env="../envs/env.test")
        with self.app.app_context():
            status = Status()
            status.last_import_album_id = 1
            db.session.add(status)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_heif(self) -> None:
        image = Image.open("tests/rosengarten.heic")
        assert image is not None
        exif_raw = image.getexif()
        assert exif_raw is not None
        exif_data = get_labeled_exif(exif_raw)
        assert exif_data is not None
        geotags = get_geotagging(exif_raw)
        assert geotags is not None
        (lat, long)  = get_lat_lon(geotags)
        assert lat
        assert long
        location = geolocator.reverse((lat, long), timeout=10)
        assert location
        address = location.raw['address']
        assert address['country_code'] == "it"
        

    def test_conversion(self):
        image = Image.open("tests/rosengarten.heic")
        out = io.BytesIO()
        image.save(out, format="JPEG")
        ims = Image.open(out)
        ims.save("tests/tt.jpg")

    def test_create_asset(self):
         with self.app.app_context():
            id = create_asset("tests/rosengarten.heic")
            photo = Asset.query.get(id)        
            assert photo
            resolve_address(photo.id)
            assert photo.gps.country_code == 'it'
            delete_asset(photo)

    def test_preview(self):
         with self.app.app_context():
            create_asset("tests/rosengarten.heic")
            photo = Asset.query.first()        
            create_preview(photo.id)
            assert os.path.exists("tests/400/high_res/tests/rosengarten.heic.jpg")
            assert os.path.exists("tests/400/low_res/tests/rosengarten.heic.jpg")
            assert os.path.exists("tests/2160/high_res/tests/rosengarten.heic.jpg")

            delete_asset(photo)
            #shutil.rmtree("tests/400")
            #shutil.rmtree("tests/2160")


    def test_orientation(self):
         with self.app.app_context():
            create_asset("tests/rot180.heic")
            photo = Asset.query.first()        
            create_preview(photo.id)

if __name__ == '__main__':
    unittest.main()
