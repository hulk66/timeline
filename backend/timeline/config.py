'''
Copyright (C) 2021, 2022 Tobias Himstedt


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

dotenv.load_dotenv(override=True, verbose=True)

DEBUG = False
TESTING = False
SECRET_KEY = os.getenv("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
POLLING = os.getenv("POLLING")
ASSET_PATH = os.getenv("ASSET_PATH")
PREVIEW_PATH = os.getenv("PREVIEW_PATH")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
# CELERY_SINGLETON_BACKEND_URL = CELERY_RESULT_BACKEND
INITIAL_SCAN = os.getenv("INITIAL_SCAN")

FACE_CLUSTER_EPSILON = os.getenv("FACE_CLUSTER_EPSILON")
FACE_CLUSTER_MIN_SAMPLES = os.getenv("FACE_CLUSTER_MIN_SAMPLES")
FACE_CLUSTER_MAX_FACES = os.getenv("FACE_CLUSTER_MAX_FACES")
FACE_DISTANCE_VERY_SAFE = os.getenv("FACE_DISTANCE_VERY_SAFE")
FACE_DISTANCE_SAFE = os.getenv("FACE_DISTANCE_SAFE")
FACE_DISTANCE_MAYBE = os.getenv("FACE_DISTANCE_MAYBE")

LOG_PATH = os.getenv("LOG_PATH")
CREATE_DATABASE = True
DB_HOST = os.getenv("DB_HOST")
DB_SUPER_USER = os.getenv("DB_SUPER_USER_PW")
CREATE_DATABASE = os.getenv("CREATE_DATABASE")
COMPUTE_SECTIONS_EVERY_MINUTES = os.getenv("COMPUTE_SECTIONS_EVERY_MINUTES")
GROUP_FACES_EVERY_MINUTES = os.getenv("GROUP_FACES_EVERY_MINUTES")
MATCH_FACES_EVERY_MINUTES = os.getenv("MATCH_FACES_EVERY_MINUTES")
OBJECT_DETECTION_MODEL_PATH = os.getenv("OBJECT_DETECTION_MODEL_PATH")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
PROCESSING_QUEUE_SECTIONING_TRESHOLD = os.getenv("PROCESSING_QUEUE_SECTIONING_TRESHOLD")

CACHE_TYPE="RedisCache"
CACHE_REDIS_HOST=os.getenv("REDIS_HOST")
CACHE_REDIS_PORT=6379

VIDEO_TRANSCODE_ON_DEMAND=os.getenv("VIDEO_TRANSCODE_ON_DEMAND", "True")
EVENT_MIN_SAMPLES=os.getenv("EVENT_MIN_SAMPLES", "50") 
EVENT_HOURS_EPSILON=os.getenv("EVENT_HOURS_EPSILON", "24")

SECTION_TARGET_SIZE=os.getenv("SECTION_TARGET_SIZE", "300")

FFMPEG_HWACCEL=os.getenv("FFMPEG_HWACCEL", "libx264")

APPLICATION_ROOT=os.getenv("TIMELINE_BASEPATH", "/timeline")

FLASK_CORS=os.getenv("FLASK_CORS", False)
