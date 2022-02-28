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

import flask
from flask import Blueprint
from timeline.extensions import celery

blueprint = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)


# ----for debugging only

@blueprint.route('/reset_learning')
def reset_learning():
    celery.send_task("timeline.tasks.match_tasks.reset_person", queue="beat")
    # reset_persons.apply_async((), queue="beat")
    return flask.jsonify(True)


@blueprint.route('/group_faces', methods=['GET'])
def group_faces_req():
    celery.send_task(
        "Group Faces", queue="beat")
    return flask.jsonify(True)


@blueprint.route('/compute_sections', methods=['GET'])
def trigger_section_compute():
    logger.debug("trigger new section computation")
    celery.send_task(
        "timeline.tasks.crud_tasks.compute_sections", queue="beat")
    return flask.jsonify(True)


@blueprint.route('/match_unknown_faces', methods=['GET'])
def trigger_match_unknown_faces():
    logger.debug("trigger match unknown faces")
    # match_all_unknown_faces.apply_async((), queue="beat")
    celery.send_task(name="Match all unknown Faces", queue="beat")

    return flask.jsonify(True)

@blueprint.route('/recreatePreviews', methods=['GET'], defaults={'dimension': 400, 'low_res':True})
@blueprint.route('/recreatePreviews/<int:dimension>/<int:low_res>', methods=['GET'])
def recreate_previews(dimension, low_res):
    logger.debug("Trigger recreation of previews for size %d", dimension)
    celery.send_task("Recreate Previews", args=(dimension, low_res), queue="process")   
    return flask.jsonify(True)
    

@blueprint.route('/face_background_tasks', methods=['GET'])
def trigger_face_background_job():
    logger.debug("Trigger face matching background jobs")
    celery.send_task("timeline.tasks.match_tasks.do_background_face_tasks",  queue="beat")   


@blueprint.route('/split_filename_path', methods=['GET'])
def split_filename_and_path():
    logger.debug("Trigger filename and path correction")
    celery.send_task("Split path and filename", queue="process")   
    return flask.jsonify(True)

@blueprint.route('/recreate_exif', methods=['GET'], defaults={'overwrite': True})
@blueprint.route('/amend_exif', methods=['GET'], defaults={'overwrite': False})
def recreate_exif_data(overwrite):
    logger.debug("Recreate Exif Data")
    celery.send_task("Extract Exif Data for all assets", args=(overwrite,), queue="process")   
    return flask.jsonify(True)

@blueprint.route('/resync_assets', methods=['GET'])
def resync_assets():
    logger.debug("Resync assets")
    celery.send_task("Resync assets",  queue="process")   
    return flask.jsonify(True)


# def remove_all_tasks():
#     celery.control.purge()

#     # remove active tasks
#     jobs = active()
#     if jobs:
#         for hostname in jobs:
#             tasks = jobs[hostname]
#             for task in tasks:
#                 celery.control.revoke(task['id'], terminate=True)

#     # remove reserved tasks
#     jobs = reserved()
#     if jobs:
#         for hostname in jobs:
#             tasks = jobs[hostname]
#             for task in tasks:
#                 celery.control.revoke(task['id'], terminate=True)

# @blueprint.route('/reset_all', methods=['GET'])
# def reset_all():

#     logger.debug("resetting all")
#     remove_all_tasks()
#     Face.query.delete()
#     Person.query.delete()
#     Exif.query.delete()
#     for p in asset.query.all():
#         p.things = []
#     asset.query.delete()
#     GPS.query.delete()
#     Section.query.delete()
#     status = Status.query.first()
#     status.face_clustering = False
#     status.sections_dirty = False
#     status.computing_sections = False
#     db.session.commit()
#     path = current_app.config.get("asset_PATH")
#     inital_scan(path)
#     return flask.jsonify(True)

# @blueprint.route('/face/match_known/<int:id>', methods=['GET'])
# def match_known_face(id):
#     match_known_face(id)
#     return flask.jsonify(True)
