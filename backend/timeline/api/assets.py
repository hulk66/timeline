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

import datetime
from timeline.util.gps import get_labeled_exif
import flask
import io
from flask import Blueprint, abort

from timeline.tasks.crud_tasks import create_preview
from timeline.util.image_ops import exif_transpose
import logging
from timeline.domain import Asset, Status, Album, Person, AssetType
from flask import request
from PIL import Image
from pathlib import Path
from timeline.util.path_util import get_full_path, get_preview_path
from timeline.extensions import db
from timeline.util.path_util import get_full_path
import os
from flask import current_app
from werkzeug.utils import secure_filename


blueprint = Blueprint("assets", __name__, url_prefix="/assets")
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


def asset_by_path(path):
    logger.debug("asset by path %s", path)
    # p = blueprint.url_prefix[1:] + "/" + path
    return Asset.query.filter(Asset.path == path).first()



@blueprint.route('/full/<path:path>', methods=['GET'])
def asset(path):
    logger.debug("asset full")
    # path_without_ext, _ = os.path.splitext(path)
    asset = asset_by_path(path)
    if asset is not None:
        if asset.is_photo():
            p = get_preview_path(asset.path, ".jpg", "2160", "high_res")
            image = Image.open(p)
            return send_image(image, fullscreen=True, last_modified=asset.created)
        #elif asset.is_video():
        #    p = get_preview_path(asset.path, ".mp4", "video", "full")
        #    f = open(p, "rb")
        #    return flask.send_file(f, mimetype="video/mp4")
        else:
            return flask.redirect('/404')

def send_video(p):
    if os.path.exists(p):
        f = open(p, "rb")
        return flask.send_file(f, mimetype="video/mp4")
    else:
        abort(404)


@blueprint.route('/video/full/<path:path>', methods=['GET'])
def video(path):
    logger.debug("return video")
    path,_ = os.path.splitext(path)
    asset = asset_by_path(path)
    p = get_preview_path(asset.path, ".mp4", "video", "full")
    return send_video(p)

@blueprint.route('/video/preview/<path:path>', methods=['GET'])
def video_preview(path):
    logger.debug("return video")
    path,_ = os.path.splitext(path)
    asset = asset_by_path(path)
    p = get_preview_path(asset.path, ".mp4", "video", "preview")
    return send_video(p)


@blueprint.route('/preview/<int:max_dim>/<resolution>/<path:path>', methods=['GET'])
def asset_preview(max_dim, resolution, path):
    logger.debug("asset preview: %s", path)
    # path_without_ext, _ = os.path.splitext(path)
    asset = asset_by_path(path)
    if asset is None:
        return flask.redirect('/404')

    preview_path = Path(get_preview_path(asset.path, ".jpg", str(max_dim), resolution))
    if not preview_path.exists():
        create_preview(asset.id)

    return flask.send_file(preview_path.absolute())

@blueprint.route('/preview_p/<int:max_dim>', methods=['GET'])
def asset_preview_by_rp(max_dim):
    logger.debug("asset preview")
    path = request.args.get("path")
    asset = asset_by_path(path)
    if asset is None:
        return flask.redirect('/404')

    preview_path = Path(get_preview_path(asset.path, str(max_dim)))
    if not preview_path.exists():
        create_preview(asset.id)

    return flask.send_file(preview_path.absolute())


def _remove_asset(id, physically):
    asset = Asset.query.get(id)
    logger.debug("Remove asset %s from catalog", asset.path)
    asset.ignore = True
    asset.albums = []
    asset.exif = []
    asset.section = None
    asset.faces = []
    asset.gps = None
    asset.things = []
    status = Status.query.first()
    status.sections_dirty = True

    # remove empty albums
    albums = Album.query.filter(Album.assets == None)
    for album in albums:
        db.session.delete(album)
    
    # same for persons
    for person in Person.query.filter(Person.faces == None):
        db.session.delete(person)


    if physically:
        path = get_full_path(asset.path)
        os.remove(path)
        db.session.delete(asset)

    # todo remove previews
    db.session.commit()


# should actually be a DELETE request
@blueprint.route('/remove', methods=['POST'])
def remove_assets():

    req_data = request.get_json()
    ids = req_data["pids"]
    physically = req_data["physically"]
    for id in ids:
        _remove_asset(id, physically)
    return flask.jsonify(True)


@blueprint.route('/removeFromCatalog/<int:id>', methods=['GET'], defaults={'physically': False})
@blueprint.route('/removePhysically/<int:id>', methods=['GET'], defaults={'physically': True})
def delete_asset(id, physically):
    _remove_asset(id, physically)
    db.session.commit()
    return flask.jsonify(True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/upload', methods=['POST'])
def upload():
    logger.debug("Upload files")
    asset_path = current_app.config['asset_PATH']
    upload_folder = current_app.config['UPLOAD_FOLDER']
    files = request.files.getlist("files")
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)   
            logger.debug("Upload %s", filename)

            in_memory  = io.BytesIO()
            file.save(in_memory)  
            image = Image.open(in_memory)
            exif_raw = image.getexif()
            exif_data = get_labeled_exif(exif_raw)
            dt = datetime.datetime.today()
            if "DateTimeOriginal" in exif_data:
                date_time = exif_data["DateTimeOriginal"]

                try:
                    # set asset date
                    dt = datetime.datetime.strptime(str(date_time), "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    logger.error("%s can not be parsed as Date for %s",
                                str(date_time), filename)
            # logger.debug("Save file under %s/%s/%d/%d/%s", asset_path, upload_folder, dt.year, dt.month, filename)
            dest_filename = os.path.join(asset_path, upload_folder, str(dt.year), str(dt.month), filename)
            os.makedirs(os.path.dirname(dest_filename), exist_ok=True)
            fout = open(dest_filename, "wb")
            fout.write(in_memory.getbuffer())
            fout.close()

    return flask.jsonify(True)
