
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
            
            
if __name__ == '__main__':
    unittest.main()
