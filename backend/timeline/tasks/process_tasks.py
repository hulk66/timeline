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
from pymysql.err import InternalError, OperationalError
from celery import signature
logger = logging.getLogger(__name__)


# retry in some cases the database throws a lock error
@celery.task(autoretry_for=(InternalError, OperationalError), name="Process Photo", ignore_result=True)
def new_photo(path):
    if '@eaDir' in path or '@__thumb' in path or "@Recycle" in path:
        logger.debug(
            "Not taking %s into account as this is some QNAP or Synology related file", path)
    else:
        # logger.debug("Start processing photo %s", path)
        photo_id = create_photo(path)
        if photo_id:
            photo = Photo.query.get(photo_id)
            create_preview(photo.path, 400,  True)
            create_preview(photo.path, 2160, False)
            
            celery.send_task("Check GPS", (photo_id,), queue="analyze")
            celery.send_task("Face Detection", (photo_id,), queue="analyze")
            celery.send_task("Object Detection", (photo_id,), queue="analyze")
            celery.send_task("Quality Assessment", (photo_id,), queue="analyze")

            # celery.send_task("timeline.tasks.iq_tasks.brisque_score", (photo_id,), queue="iq")

