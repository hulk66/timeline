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

blueprint = Blueprint("albums", __name__, url_prefix="/albums")
logger = logging.getLogger(__name__)

@blueprint.route('/all', methods=['GET'])
def get_all_albums():
    logger.debug("get all albums")
    albums = Album.query.order_by(Album.name).all()
    return flask.jsonify([a.to_dict() for a in albums])


@blueprint.route('/create', methods=['POST'])
def create_new_album():
    req_data = request.get_json()
    album_name = req_data.get("albumName")
    photo_ids = req_data["pids"]
    album = Album()
    album.name = album_name
    for id in photo_ids:
        photo = Photo.query.get(id)
        album.photos.append(photo)
    db.session.add(album)
    db.session.commit()    
