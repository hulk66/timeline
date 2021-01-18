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

from timeline.app import init_celery, create_app, setup_logging
from timeline.tasks.face_tasks import init_face_services
from timeline.tasks.classify_tasks import init_classify_services
from celery.signals import celeryd_after_setup
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
from timeline.tasks.crud_tasks import schedule_next_compute_sections
from timeline.tasks.face_tasks import schedule_next_grouping, schedule_next_match_all_unknown_faces
from timeline.extensions import celery 

flask_app = create_app()
# app = init_celery(flask_app)
app = celery
setup_logging(flask_app, 'worker.log')

@celeryd_after_setup.connect
def setup_direct_queue(sender, instance, **kwargs):
    init_face_services()
    init_classify_services(flask_app.config['OBJECT_DETECTION_MODEL_PATH'])

    schedule_next_compute_sections()
    schedule_next_grouping()
    schedule_next_match_all_unknown_faces()
