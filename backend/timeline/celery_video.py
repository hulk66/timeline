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

from celery.signals import celeryd_after_setup, worker_process_init, worker_init

from timeline.util.path_util import get_preview_path
from timeline.util.path_util import get_full_path
from timeline.domain import Asset, TranscodingStatus
from timeline.app import create_app, setup_logging
from timeline.extensions import db, celery
import logging
import os
import ffmpeg

flask_app = create_app()
setup_logging("timeline", flask_app, 'video_worker.log')
logger = logging.getLogger(__name__) 
#nice_ffmpeg = ["nice", "-n", "20", "ffmpeg"]
nice_ffmpeg = "ffmpeg"

@worker_process_init.connect
def init_worker(**kwargs):
    """
        When Celery fork's the parent process, the db engine & connection pool is included in that.
        But, the db connections should not be shared across processes, so we tell the engine
        to dispose of all existing connections, which will cause new ones to be opend in the child
        processes as needed.
        More info: https://docs.sqlalchemy.org/en/latest/core/pooling.html#using-connection-pools-with-multiprocessing
    """
    # The "with" here is for a flask app using Flask-SQLAlchemy.  If you don't
    # have a flask app, just remove the "with" here and call .dispose()
    # on your SQLAlchemy db engine.
    logger.debug("Initialize Worker")
    with flask_app.app_context():
        db.engine.dispose()


@celery.task(name="Create Preview Video")
def create_preview_video(asset_id, max_dim: int) -> None:
    asset = Asset.query.get(asset_id)
    path = get_full_path(asset.path)

    # generate a static jpg preview image
    logger.debug("Create jpg preview %s", asset.path)
    preview_path = get_preview_path(
        asset.path, ".jpg", str(max_dim), "high_res")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    ffmpeg.input(path).filter("scale", -2, max_dim).output(preview_path, map_metadata=0, threads=1,
                                                           movflags="use_metadata_tags", vframes=1, loglevel="error").overwrite_output().run(cmd=nice_ffmpeg)

    # also generate a very low res resolution preview jpg for fast loading
    #preview_path = get_preview_path(
    #    asset.path, ".jpg", str(max_dim), "low_res")
    #os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    #ffmpeg.input(path).filter("scale", -2, max_dim/10).output(preview_path, map_metadata=0, threads=1,
    #                                                          movflags="use_metadata_tags", vframes=1, loglevel="error").overwrite_output().run(cmd=nice_ffmpeg)

    # finally generate a preview mp4 and strip the audio
    logger.debug("Create mp4 preview for hovering %s", asset.path)
    preview_path = get_preview_path(asset.path, ".mp4", "video", "preview")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    ffmpeg.input(path).filter("scale", -2, max_dim).output(preview_path, map_metadata=0, loglevel="error",
                                                           vcodec="libx264",
                                                           movflags="+faststart +use_metadata_tags",
                                                           pix_fmt="yuv420p", t=5).overwrite_output().global_args("-an").run(cmd=nice_ffmpeg)

    asset.video_preview_generated = True
    db.session.commit()

@celery.task(name="Create Fullscreen Video")
def create_fullscreen_video(asset_id) -> None:
    asset = Asset.query.get(asset_id)

    logger.debug("Convert to browser compatible mp4 %s", asset.path)

    if asset.video_fullscreen_transcoding_status == TranscodingStatus.STARTED or asset.video_fullscreen_transcoding_status == TranscodingStatus.DONE:
        logger.debug("Nothing to be done. Video is either already transcoded or manually triggered")
        return
        
    path = get_full_path(asset.path)
    asset.video_fullscreen_transcoding_status = TranscodingStatus.STARTED
    asset.video_fullscreen_generated_progress = 50 # replace this later when we have a progress
    db.session.commit()

    # For the conversion with ffmpeg limit everything to just 1 thread
    # otherwise it will span multiple thread per conversion
    # this wil slow down the system too much

    # convert in any case (mp4 or mov); not all mp4 are playable in the browser
    # convet mov to mp4 to have it playable in the browser
    preview_path = get_preview_path(asset.path, ".mp4", "video", "full")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    ffmpeg.input(path).output(preview_path, loglevel="error", vcodec="libx264", acodec="aac",
                              pix_fmt="yuv420p", movflags="faststart +use_metadata_tags").overwrite_output().run(cmd=nice_ffmpeg)

    asset.video_fullscreen_transcoding_status = TranscodingStatus.DONE
    asset.video_fullscreen_generated_progress = 100 # replace this later when we have a progress
    db.session.commit()

