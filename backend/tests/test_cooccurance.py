import context

from timeline.domain import Asset, Status, Face, Person
import unittest
from datetime import datetime
from timeline.app import create_app
from timeline.extensions import db
from timeline.tasks.crud_tasks import create_asset
from timeline.tasks.face_tasks import find_faces, find_faces2, detect_facial_expression, detect_age, detect_gender, init_face_age_gender, init_vgg_face
from timeline.api.views import crop_face
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import get_full_path
import time
from sqlalchemy import and_, or_
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
from sqlalchemy import desc
import csv

class TestCoOccurance(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")


    def test_extract_cooccurance(self):
        with self.app.app_context():

            top20 = db.session.query(Person.id.label("person_id"), Person.name, db.func.count(Face.id).label("count")).join(Person).filter(Face.confidence_level > 1).order_by(desc("count")).group_by("person_id").limit(20).all()
            # assetWithFaces = db.session.query(Face.asset_id).filter(and_(Face.confidence_level > 1, Face.person_id != None)).group_by(Face.asset_id).having(db.func.count(Face.asset_id) = 4)
            
            names = list(map(lambda e: e[1], top20))            
            names.insert(0, "Asset ID")
            ids = list(map(lambda e: e[0], top20))            
            names_lookup = {}
            for t in top20:
                names_lookup[t[0]] = t[1]

            asset_ids = Asset.query.join(Face).join(Person).filter(Person.id.in_(ids)).with_entities(Asset.id)
            with open('occurance2.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=names)
                writer.writeheader()
                counter = 0
                for asset_id in asset_ids:
                    if counter % 100 == 0:
                        print (counter)
                    counter += 1
                    asset_id = asset_id[0]
                    row = {}
                    row["Asset ID"] = asset_id
                    person_ids = Person.query.join(Face).join(Asset).filter(Asset.id == asset_id).with_entities(Person.id).all()                            
                    person_ids = list(map(lambda p: p[0], person_ids))
                    for id in ids:
                        # person = Person.query.get(id)
                        name = names_lookup[id]
                        if id in person_ids:
                            row[name] = 1
                        else:
                            row[name] = 0
                    writer.writerow(row)


    def xxtest_co_occurance(self):
        with self.app.app_context():
            # first find top 10 faces
            top10 = db.session.query(Person.id.label("person_id"), Person.name, db.func.count(Face.id).label("count")).join(Person).filter(Face.confidence_level > 1).order_by(desc("count")).group_by("person_id")
            # assetWith4Faces = db.session.query(db.func.count(Face.asset_id), Face.asset_id).group_by(Face.asset_id).having(db.func.count(Face.asset_id) == 4)
            assetWith4Faces = db.session.query(Face.asset_id).filter(and_(Face.confidence_level > 1, Face.person_id != None)).group_by(Face.asset_id).having(db.func.count(Face.asset_id) == 4)
            
            for element in assetWith4Faces:
                asset_id = element[0]
                # asset = Asset.query.get(asset_id)
                person_ids_tupel = Person.query.join(Face).join(Asset).filter(Asset.id == asset_id, Face.confidence_level > 1).order_by(Person.id).with_entities(Person.id)
                person_ids = map(lambda e: e[0], person_ids_tupel)


if __name__ == '__main__':
    unittest.main()
