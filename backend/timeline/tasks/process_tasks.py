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

import logging

from timeline.domain import Photo
from timeline.extensions import celery
from timeline.tasks.crud_tasks import create_photo, create_preview
from timeline.tasks.geo_tasks import set_display_address
from timeline.tasks.face_tasks import find_faces
from timeline.tasks.classify_tasks import analyze_photo
from pathlib import Path
from pymysql.err import InternalError
from timeline.tasks.iq_tasks import predict

logger = logging.getLogger(__name__)

# retry in some cases the database throws a lock error
@celery.task(autoretry_for=(InternalError,), name="Process Photo", ignore_result=True)
def new_photo(path):
    if '@eaDir' in path or '@__thumb' in path or "@Recycle" in path:
        logger.debug("Not taking %s into account as this is some QNAP or Synology related file", path)
    else:
        logger.debug("Start processing photo %s", path)
        photo_id = create_photo(path)
        if photo_id:
            photo = Photo.query.get(photo_id)
            set_display_address.apply_async((photo_id,), queue='geo_req')
            find_faces.apply_async((photo_id,), queue='face')
            analyze_photo.apply_async((photo_id,), queue='thing')
            create_preview(photo.path, 200)
            create_preview(photo.path, 2160)
            predict.apply_async((photo_id,), queue="iq")

@celery.task(name="Initial Scan", ignore_result=True)
def inital_scan(path, patterns=["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]):
    logger.debug("Performing initial scan for directory %s", path)
    files = []
    for file_type in patterns:
        files.extend(Path(path).rglob(file_type))

    logger.info("Found %i files", len(files))
    for file in files:
        new_photo.apply_async((str(file),), queue="process")
    logger.debug("Initial Scan done")