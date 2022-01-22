import context

from timeline.domain import Asset, Status, Face
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

class TestDateClustering(unittest.TestCase):

    def setUp(self):
        self.app = create_app(testing=True, env="../envs/env.ds")

    def test_date_cluster(self):
        with self.app.app_context():
            start_date = datetime(2021, 1, 1)
            end_date = datetime(2022, 1, 1)
            dates_in_range = Asset.query.filter( and_(Asset.created >= start_date, Asset.created < end_date)).with_entities(Asset.created)
            timestamps = [datetime.timestamp(d[0]) for d in dates_in_range.all()]
            assert timestamps
            x = np.array(timestamps).reshape(-1, 1)
            x  = StandardScaler().fit_transform(x)
            db = DBSCAN(eps = 0.5, min_samples=10).fit(x)
            n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
            assert n_clusters > 0
            n_noise = list(db.labels_).count(-1)
            assert n_noise > 0
            print()
            print(n_clusters)
            for cluster in range(n_clusters - 1):
                indices = np.where(db.labels_ == cluster)
                print("------- Cluster ", cluster)
                for index in indices[0]:
                    ts = timestamps[index]
                    print(datetime.fromtimestamp(ts), end=", ")


if __name__ == '__main__':
    unittest.main()
