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

import flask
import io
from flask import Blueprint

from timeline.tasks.crud_tasks import create_preview
from timeline.util.image_ops import exif_transpose
import logging
from timeline.domain import Photo, Status, Album, Person
from flask import request
from PIL import Image
from pathlib import Path
from timeline.util.path_util import get_full_path, get_preview_path
from timeline.extensions import db
from timeline.util.path_util import get_full_path
import os

blueprint = Blueprint("photos", __name__, url_prefix="/photos")
logger = logging.getLogger(__name__)


def send_image(image, transpose=True, last_modified=None, fullscreen=False):
    result = image
    if transpose:
        try:
            result = exif_transpose(image)
        except Exception as exc:
            logger.exception("Can't transpose image by Exif data: %s", str(exc))
    if fullscreen:
        result.thumbnail((2160, 2160), Image.ANTIALIAS)
    img_io = io.BytesIO()
    if fullscreen:
        result.save(img_io, 'JPEG')
        mimetype = 'image/jpeg'
    else:
        result.save(img_io, 'PNG')
        mimetype = 'image/png'
    img_io.seek(0)
    return flask.send_file(img_io, mimetype=mimetype, last_modified=last_modified)


def photo_by_path(path):
    logger.debug("photo by path %s", path)
    # p = blueprint.url_prefix[1:] + "/" + path
    return Photo.query.filter(Photo.path == path).first()


@blueprint.route('/full/<path:path>', methods=['GET'])
def photo(path):
    logger.debug("photo full")
    photo = photo_by_path(path)
    if photo is not None:
        # p = get_full_path(photo.path, resolution)
        p = get_preview_path(photo.path, "2160", "high_res")
        image = Image.open(p)
        return send_image(image, fullscreen=True, last_modified=photo.created)
    return flask.redirect('/404')


@blueprint.route('/preview/<int:max_dim>/<resolution>/<path:path>', methods=['GET'])
def photo_preview(max_dim, resolution, path):
    logger.debug("photo preview: %s", path)
    photo = photo_by_path(path)
    if photo is None:
        return flask.redirect('/404')

    preview_path = Path(get_preview_path(photo.path, str(max_dim), resolution))
    if not preview_path.exists():
        create_preview(photo.path, max_dim, True)

    return flask.send_file(preview_path.absolute())

@blueprint.route('/preview_p/<int:max_dim>', methods=['GET'])
def photo_preview_by_rp(max_dim):
    logger.debug("photo preview")
    path = request.args.get("path")
    photo = photo_by_path(path)
    if photo is None:
        return flask.redirect('/404')

    preview_path = Path(get_preview_path(photo.path, str(max_dim)))
    if not preview_path.exists():
        create_preview(photo.path, max_dim)

    return flask.send_file(preview_path.absolute())


def _remove_photo(id, physically):
    photo = Photo.query.get(id)
    logger.debug("Remove photo %s from catalog", photo.path)
    photo.ignore = True
    photo.albums = []
    photo.exif = []
    photo.section = None
    photo.faces = []
    photo.gps = None
    photo.things = []
    status = Status.query.first()
    status.sections_dirty = True
    db.session.delete(photo)

    # remove empty albums
    albums = Album.query.filter(Album.photos == None)
    for album in albums:
        db.session.delete(album)
    
    # same for persons
    for person in Person.query.filter(Person.faces == None):
        db.session.delete(person)


    if physically:
        path = get_full_path(photo.path)
        os.remove(path)
    # todo remove previews
    db.session.commit()


# should actually be a DELETE request
@blueprint.route('/remove', methods=['POST'])
def remove_photos():

    req_data = request.get_json()
    ids = req_data["pids"]
    physically = req_data["physically"]
    for id in ids:
        _remove_photo(id, physically)
    return flask.jsonify(True)


@blueprint.route('/removeFromCatalog/<int:id>', methods=['GET'], defaults={'physically': False})
@blueprint.route('/removePhysically/<int:id>', methods=['GET'], defaults={'physically': True})
def delete_photo(id, physically):
    _remove_photo(id, physically)
    db.session.commit()
    return flask.jsonify(True)