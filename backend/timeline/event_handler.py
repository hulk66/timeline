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
import os

from watchdog.events import PatternMatchingEventHandler

from timeline.tasks.crud_tasks import delete_asset, modify_asset
from timeline.tasks.process_tasks import new_asset

logger = logging.getLogger(__name__)


class EventHandler(PatternMatchingEventHandler):
    patterns = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.mov", "*.MOV", "*.mp4", "*.MP4"]
    ignore = ["*@eaDir*", "*@__thumb*", "*@Recycle*"]

    base_path = None

    def __init__(self, base_path):
        super(EventHandler, self).__init__(patterns=self.patterns, ignore_patterns=self.ignore)
        self.base_path = base_path

    def on_created(self, event):
        abs_path = os.path.abspath(event.src_path)
        logger.debug("New File: %s", abs_path)
        # new_asset.delay(event.src_path)
        new_asset.apply_async( (event.src_path,), queue='process')
        # new_asset(event.src_path)

    def on_deleted(self, event):
        path = os.path.abspath(event.src_path)
        logger.debug("Deleted file: %s", path)
        # delete_asset.delay(event.src_path)
        delete_asset.apply_async( (event.src_path,), queue='process')

    #def on_modified(self, event):
    #    path = os.path.abspath(event.src_path)
    #    logger.debug("on_modified: %s", path)
    #    # modify_asset.delay(event.src_path)
    #    # modify_asset.apply_async( (event.src_path,), queue='process')

    def on_moved(self, event):
        path = os.path.abspath(event.src_path)
        logger.debug("Move File: %s", path)
        # dest_path = os.path.abspath(event.dest_path)
        # move_asset.delay(event.src_path, event.dest_path)
        modify_asset.apply_async( (event.src_path, event.dest_path), queue='process')
