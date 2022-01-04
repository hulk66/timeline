from timeline.domain import Asset, Status, Face
import unittest
from timeline.app import create_app
from timeline.extensions import db
from timeline.tasks.crud_tasks import create_asset
from timeline.tasks.face_tasks import find_faces, find_faces2, detect_facial_expression, detect_age, detect_gender, init_face_age_gender, init_vgg_face
from timeline.api.views import crop_face
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import get_full_path
import time

class TestCrudAndFace(unittest.TestCase):

    def setUp(self):
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

    def test_create_asset(self):
        with self.app.app_context():
            create_asset("tests/gps.jpg")
            photo = Asset.query.first()
            assert photo


    def test_facial_expression(self):
        init_vgg_face()
        init_face_age_gender();
        with self.app.app_context():
            id = create_asset("tests/friends.jpeg")
            find_faces2(id, False)
            for face in Face.query:
                detect_facial_expression(face.id)
                assert face.emotion
                assert face.emotion_confidence
                #detect_age(face.id)
                #assert face.predicted_age is not None
                #detect_gender(face.id)
                #assert face.predicted_gender is not None                

    def test_face_detection(self):
        init_vgg_face()
        init_face_age_gender();
        with self.app.app_context():
            id = create_asset("tests/mm.jpg")
            find_faces2(id, False)

            face1 = Face.query.get(1)
            face2 = Face.query.get(2)
            assert face1
            assert face2

            path = get_full_path(face1.asset.path)
            image = read_and_transpose(path)

            face_image1 = crop_face(image, 200, face1.x, face1.y, face1.w, face1.h)
            assert face_image1

            face_image2 = crop_face(image, 200, face2.x, face2.y, face2.w, face2.h)
            assert face_image2
            # should show Merkel and Macron
            # face_image1.show()
            # face_image2.show()
