import unittest
from PIL import Image
from pillow_heif import register_heif_opener
from timeline.tasks.crud_tasks import _extract_exif_data
from timeline.util.gps import (get_exif_value, get_geotagging, get_gps_data,
                               get_labeled_exif, get_lat_lon)
from timeline.tasks.geo_tasks import geolocator

class TestHeif(unittest.TestCase):

    def setUp(self):
        register_heif_opener()

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
        
