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

import logging
from timeline.domain import Asset
from timeline.extensions import celery
from timeline.tasks.crud_tasks import create_asset, create_preview
from timeline.util.asset_creation_result import AssetCreationResult
from timeline.util.asset_utils import dedup_header
from pymysql.err import InternalError, OperationalError
from celery import signature
logger = logging.getLogger(__name__)


# retry in some cases the database throws a lock error
@celery.task(autoretry_for=(InternalError, OperationalError), name="Process Asset", ignore_result=True)
def new_asset(path):
    if '@eaDir' in path or '@__thumb' in path or "@Recycle" in path or "@Transcode" in path:
        logger.debug(
            "Not taking %s into account as this is some QNAP or Synology related file", path)
    else:
        logger.debug("Start processing asset %s", path)
        result : AssetCreationResult = create_asset(path)
        if result.asset_id and result.created_in_db:
            logger.debug("Scheduling consequent tasks for asset %s", path)
            asset = Asset.query.get(result.asset_id)
            create_preview(result.asset_id)
            celery.send_task("Check GPS", (result.asset_id,), queue="geo", headers=dedup_header(result.asset.path, "geo"))
            if asset.is_photo():
                celery.send_task("Face Detection", (result.asset_id,), queue="analyze", headers=dedup_header(result.asset.path, "analyze-face"))
                celery.send_task("Object Detection", (result.asset_id,), queue="analyze", headers=dedup_header(result.asset.path, "analyze-obj"))
                celery.send_task("Quality Assessment", (result.asset_id,), queue="analyze", headers=dedup_header(result.asset.path, "analyze-quality"))

            # celery.send_task("timeline.tasks.iq_tasks.brisque_score", (asset_id,), queue="iq", headers=dedup_header(result.asset.path, "iq-brisque"))

