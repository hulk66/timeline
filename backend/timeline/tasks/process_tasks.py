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
#from timeline.tasks.geo_tasks import set_display_address
#from timeline.tasks.face_tasks import find_faces
#from timeline.tasks.classify_tasks import analyze_photo
from pymysql.err import InternalError
#from timeline.tasks.iq_tasks import predict_quality, brisque_score

logger = logging.getLogger(__name__)


# retry in some cases the database throws a lock error
@celery.task(autoretry_for=(InternalError,), name="Process Photo", ignore_result=True)
def new_photo(path):
    if '@eaDir' in path or '@__thumb' in path or "@Recycle" in path:
        logger.debug(
            "Not taking %s into account as this is some QNAP or Synology related file", path)
    else:
        logger.debug("Start processing photo %s", path)
        photo_id = create_photo(path)
        if photo_id:
            photo = Photo.query.get(photo_id)
            # set_display_address.apply_async((photo_id,), queue='geo_req')
            # find_faces.apply_async((photo_id,), queue='face')
            # analyze_photo.apply_async((photo_id,), queue='thing')
            create_preview(photo.path, 400)
            create_preview(photo.path, 2160)
            # predict_quality.apply_async((photo_id,), queue="iq")
            # brisque_score.apply_async((photo_id,), queue="iq")
            
            #chain = (
            #    set_display_address.si(photo_id).set(queue="geo_req") |
            #    find_faces.si(photo_id).set(queue="face") |
            #    analyze_photo.si(photo_id).set(queue="thing") |
            #    predict_quality.si(photo_id).set(queue="iq") |
            #    brisque_score.si(photo_id).set(queue="iq")
            #)
            #chain.delay()

            celery.send_task("Checking for GPS Information", (photo_id,), queue="geo_req")
            celery.send_task("Face Detection", (photo_id,), queue="face")
            celery.send_task("Object Detection", (photo_id,), queue="thing")
            celery.send_task("timeline.tasks.iq_tasks.predict_quality", (photo_id,), queue="iq")
            celery.send_task("timeline.tasks.iq_tasks.brisque_score", (photo_id,), queue="iq")

