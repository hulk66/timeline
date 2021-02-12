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
from timeline.domain import Photo
from flask import request
from PIL import Image
from pathlib import Path
from timeline.util.path_util import get_full_path, get_preview_path


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
    # path = request.args.get("path")
    photo = photo_by_path(path)
    if photo is not None:
        p = get_full_path(photo.path)
        image = Image.open(p)
        return send_image(image, fullscreen=True, last_modified=photo.created)
    return flask.redirect('/404')


@blueprint.route('/preview/<int:max_dim>/<path:path>', methods=['GET'])
def photo_preview(max_dim, path):
    logger.debug("photo preview: %s", path)
    photo = photo_by_path(path)
    if photo is None:
        return flask.redirect('/404')

    preview_path = Path(get_preview_path(photo.path, str(max_dim)))
    if not preview_path.exists():
        create_preview(photo.path, max_dim)

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
