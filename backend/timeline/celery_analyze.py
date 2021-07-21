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

from celery.signals import celeryd_after_setup, worker_process_init

from timeline.app import create_app, setup_logging
from timeline.extensions import db, celery

from timeline.tasks.classify_tasks import init_classify_services
from timeline.tasks.face_tasks import init_vgg_face, init_face_age_gender
from timeline.tasks.iq_tasks import init_iq

flask_app = create_app()
setup_logging(flask_app, "analyze_worker.log")

@celeryd_after_setup.connect
def setup_direct_queue(sender, instance, **kwargs):
    pass

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
    with flask_app.app_context():
        db.engine.dispose()

    init_face_age_gender()
    init_iq()
    init_classify_services(flask_app.config['OBJECT_DETECTION_MODEL_PATH'])
    init_vgg_face()
