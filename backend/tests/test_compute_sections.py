import context 

from timeline.domain import Asset, Status, Face
import unittest
from timeline.app import create_app
from timeline.extensions import db
from timeline.tasks.crud_tasks import create_asset
from timeline.tasks.face_tasks import find_faces, find_faces2, detect_facial_expression, detect_age, detect_gender, init_face_age_gender, init_vgg_face
from timeline.api.views import crop_face
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import get_full_path
from timeline.tasks.crud_tasks import compute_sections


class TestComputeSections(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")

    def test_compute_sections(self):
        compute_sections()

if __name__ == '__main__':
    unittest.main()
