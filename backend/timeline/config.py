'''
Copyright (C) 2021 Tobias Himstedt


This file is part of Timeline.

Timeline is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Timeline is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

import os

import dotenv

dotenv.load_dotenv()

DEBUG = False
TESTING = False
SECRET_KEY = os.getenv("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
POLLING = os.getenv("POLLING")
PHOTO_PATH = os.getenv("PHOTO_PATH")
PREVIEW_PATH = os.getenv("PREVIEW_PATH")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
result_backend = os.getenv("CELERY_RESULT_BACKEND")
INITIAL_SCAN = os.getenv("INITIAL_SCAN")
FACE_CLUSTER_EPSILON = 0.5
FACE_CLUSTER_MIN_SAMPLES = 5
FACE_CLUSTER_MAX_FACES = 5000
LOG_PATH = os.getenv("LOG_PATH")
CREATE_DATABASE = os.getenv("LOG_PATH")
DB_HOST = os.getenv("DB_HOST")
DB_SUPER_USER = os.getenv("DB_HOST")
CREATE_DATABASE = os.getenv("CREATE_DATABASE")
COMPUTE_SECTIONS_EVERY_MINUTES = os.getenv("COMPUTE_SECTIONS_EVERY_MINUTES")
GROUP_FACES_EVERY_MINUTES = os.getenv("GROUP_FACES_EVERY_MINUTES")
MATCH_FACES_EVERY_MINUTES =  os.getenv("MATCH_FACES_EVERY_MINUTES")
OBJECT_DETECTION_MODEL_PATH=os.getenv("OBJECT_DETECTION_MODEL_PATH")
