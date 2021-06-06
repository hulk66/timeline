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
from flask import Blueprint, request
import logging
from timeline.domain import Album, Photo
from timeline.extensions import db
from timeline.api.util import list_as_json
from sqlalchemy import and_


blueprint = Blueprint("albums", __name__, url_prefix="/albums")
logger = logging.getLogger(__name__)

@blueprint.route('/all', methods=['GET'])
def get_all_albums():
    logger.debug("get all albums")
    albums = Album.query.order_by(Album.name).all()
    return flask.jsonify([a.to_dict() for a in albums])


def add_photos(album, photo_ids):
    for id in photo_ids:
        photo = Photo.query.get(id)
        album.photos.append(photo)

@blueprint.route('/create', methods=['POST'])
def create_new_album():
    req_data = request.get_json()
    album_name = req_data.get("albumName")
    photo_ids = req_data["pids"]
    album = Album()
    album.name = album_name
    add_photos(album, photo_ids)
    db.session.add(album)
    db.session.commit()    
    return flask.jsonify(album.to_dict())


@blueprint.route('/addPhotoToAlbum', methods=['POST'])
def add_photos_to_album():
    req_data = request.get_json()
    album_id = req_data.get("albumId")
    photo_ids = req_data["pids"]
    album = Album.query.get(album_id)
    add_photos(album, photo_ids)
    db.session.commit()    
    return flask.jsonify(album.to_dict())


@blueprint.route('/rename/<int:id>/<name>', methods=['GET'])
def rename(id, name):
    album = Album.query.get(id)
    album.name = name
    db.session.commit()
    return flask.jsonify(album.to_dict())
    

@blueprint.route('/remove/<int:id>', methods=['GET'])
def delete(id):
    album = Album.query.get(id)
    db.session.delete(album)
    db.session.commit()
    return flask.jsonify(True)

@blueprint.route('/info/<int:id>', methods=['GET'])
def info(id):
    album = Album.query.get(id)
    if album:
        return flask.jsonify(album.to_dict())
    return flask.jsonify(None)

@blueprint.route('/photos/<int:album_id>', defaults={'count': None}, methods=['GET'])
@blueprint.route('/photos/<int:album_id>/<int:count>', methods=['GET'])
def photos(album_id, count):
    # q = Photo.query.join(Photo.albums).filter(id == album_id)   
    # q = Photo.query.filter(Photo.albums.any(id == album_id))
    photos = Photo.query.join(Photo.albums).filter(Album.id == album_id)
    if count:
        photos = photos.limit(count)
    return list_as_json(photos, excludes=("-exif", "-gps", "-faces", "-things", "-section", "-albums"))
