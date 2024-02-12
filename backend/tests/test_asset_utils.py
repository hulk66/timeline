
import context
import unittest
from timeline.util.asset_utils import CURRENT_VERSION, populate_asset
from timeline.app import create_app
from timeline.extensions import db
from timeline.domain import Asset

class TestAssetUtils(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_asset(self):
        with self.app.app_context():
            asset: Asset = populate_asset(None, "tests/gps.jpg")
            assert asset
            assert asset.version == CURRENT_VERSION
            assert asset.checksum_type == "MD5"
            assert asset.checksum != None
            assert asset.file_size == 2275086
            
    def test_private_asset(self):
        with self.app.app_context():
            # asset: Asset = populate_asset(None, "nas/Red1/Photoes/gallery/_Parse/2015-02-18 Trip/P1050385.JPG")
            # asset: Asset = populate_asset(None, "WD/photo_dump/Photoes/gallery/_Parse/2015-07-29/20150719_164913.jpg")
            asset: Asset = populate_asset(None, "WD/main/Photoes/gallery/_Parse/2015-07-29/20150719_164913.jpg")
            # asset: Asset = populate_asset(None, "nas/Red1/Photoes/gallery/_Parse/2015-07-29/20150719_164913.jpg")
            assert asset
            # Check V1
            # assert asset.gps
            # assert asset.gps.latitude
            # assert asset.gps.longitude

            # Check V2
            assert asset.no_creation_date == False
            assert asset.version == CURRENT_VERSION
            assert asset.checksum_type == "MD5"
            assert asset.checksum != None
            assert asset.file_size == 4120151            

if __name__ == '__main__':
    unittest.main()
