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
import os
import random
from datetime import datetime
import uuid
import flask
from flask import current_app
import ffmpeg
from flask import Blueprint, request
from PIL import Image, ImageDraw
from sqlalchemy import and_, or_
from timeline.util.asset_utils import dedup_header
from timeline.util.tags_util import parse_tags, find_new_tags
from timeline.api.assets import send_image
from timeline.api.util import list_as_json, refine_query, assets_from_smart_album
from timeline.domain import (GPS, Face, Person, Asset, Section, Status, Thing,
                             asset_thing, Exif, asset_album, Album, AlbumType, Tag)
from timeline.extensions import db
from timeline.tasks.match_tasks import (assign_new_person, 
                                        distance_safe,
                                        find_all_classified_known_faces,
                                        find_closest, group_faces,
                                        match_all_unknown_faces)
from timeline.util.image_ops import read_and_transpose, resize_width
from timeline.util.path_util import get_full_path, get_preview_path
from timeline.extensions import celery


blueprint = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

exif_filter = ["FocalLength", "ExifImageWidth", "ExifImageHeight",
               "Make", "Model", "ExposureTime", "Copyright", "FNumber", "  ", "LensModel", "Artist"]


def jsonify_pagination(q, page, size):
    paginate = q.paginate(page=page, per_page=size, error_out=False)
    result = {
        "items": [item.to_dict() for item in paginate.items],
        "pages": paginate.pages,
        "total": paginate.total
    }
    json = flask.jsonify(result)
    return json


@blueprint.errorhandler(404)
def page_not_found(e):
    return "Not found"


def crop_face(image, max_dim, x, y, w, h):
    enlarge_x = 0.2
    enlarge_y = 0.2

    x1, y1, x2, y2 = x, y, x + w, y + h

    if h > w:
        d = int((h - w) / 2)
        x1 -= d
        x2 += d
    else:
        d = int((w - h) / 2)
        y1 -= d
        y2 += d
    offset_x, offset_y = w * enlarge_x, h * enlarge_y

    x1 -= int(offset_x)
    y1 -= int(offset_y)
    x2 += int(offset_x)
    y2 += int(offset_y)

    result = image.crop((x1, y1, x2, y2))

    bigsize = (result.size[0] * 3, result.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(result.size, Image.ANTIALIAS)
    result.putalpha(mask)

    # size = resize_width(result, max_dim)
    # result.thumbnail(size)
    result.thumbnail((max_dim, max_dim))
    return result


def save_preview(id, dim, image):
    preview_path = get_preview_path(str(id), ".png", "faces", str(dim))
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path)


@blueprint.route('/face/preview/<int:max_dim>/<int:id>.png', methods=['GET'])
def face_preview(id, max_dim=300):
    face = Face.query.get(id)
    if face:
        path = get_full_path(face.asset.path)
        image = read_and_transpose(path)

        result = crop_face(image, max_dim, face.x, face.y, face.w, face.h)
        save_preview(id, max_dim, result)
        # return send_image(result, transpose=False)
        return send_image(result, False, last_modified=face.created)
    return flask.redirect('/404')


@blueprint.route('/face/<int:id>', methods=['GET'])
def face(id):
    face = Face.query.get(id)
    if face is not None:
        path = get_full_path(face.asset.path)
        image = read_and_transpose(path)
        result = image.crop((face.x, face.y, face.x + face.w, face.y + face.h))
        return send_image(result, False, face.created)
    return flask.redirect('/404')


@blueprint.route('/face/by_person/<int:id>', methods=['GET'])
def face_by_person(id):
    # faces = Person.query.get(id).faces
    # faces = Face.query.filter(and_(Face.person_id == id, Face.confidence <= Face.DISTANCE_SAFE)).all()
    faces = Face.query.join(Person).filter(and_(Face.person_id == Person.id, Person.id == id, or_(
        Face.confidence <= distance_safe(), Person.confirmed == False))).all()
    return jsonify_items(faces)


@blueprint.route('/tags', methods=['GET'])
def get_all_tags():
    return jsonify_items(Tag.query.all())


@blueprint.route("/asset/tags/<int:asset_id>/<string:tags_str>", methods=["PUT"])
def set_tags(asset_id, tags_str):
    excludes = ("-exif", "-gps", "-faces", "-things", "-section")
    asset = Asset.query.get(asset_id)
    tags_to_set = parse_tags(tags_str)
    (new_tags, tags_to_create, tags_to_set) = find_new_tags(
        tags_to_set, asset.tags, Tag.query.all()
    )
    created_tags = []
    for tag_name in tags_to_create:
        tag = Tag()
        tag.name = tag_name
        tag.created = datetime.today()
        db.session.add(tag)
        created_tags.append(tag)
    asset.tags = []
    for tag in tags_to_set:
        asset.tags.append(tag)
    for tag in created_tags:
        asset.tags.append(tag)
    db.session.commit()
    return flask.jsonify(asset.to_dict(rules=excludes))


@blueprint.route("/asset/tags/<int:asset_id>/<string:tags_str>", methods=["DELETE"])
def remove_tags(asset_id, tags_str):
    excludes = ("-exif", "-gps", "-faces", "-things", "-section")
    asset = Asset.query.get(asset_id)
    tags_to_remove = parse_tags(tags_str)
    for tag in asset.tags:
        if tag.name in tags_to_remove:
            asset.tags.remove(tag)
    db.session.commit()
    return flask.jsonify(asset.to_dict(rules=excludes))


@blueprint.route('/asset/setRating/<int:asset_id>/<int:rating>', methods=['GET'])
def set_rating(asset_id, rating):
    excludes=("-exif", "-gps", "-faces", "-things", "-section")
    asset = Asset.query.get(asset_id)
    asset.stars = rating
    db.session.commit()
    return flask.jsonify(asset.to_dict(rules=excludes))

@blueprint.route('/asset/preview/<int:max_dim>/<int:id>.jpg', methods=['GET'])
def asset_preview(id, max_dim):
    logger.debug("get preview for %i", id)
    asset = Asset.query.get(id)
    if asset is None:
        return flask.redirect('/404')

    path = get_full_path(asset.path)
    if asset.is_photo():
        image = read_and_transpose(path)
        size = resize_width(image, max_dim)
        image.thumbnail(size)
    else:
        logger.debug("requested asset is a video")
        preview_path = get_preview_path(asset.path, ".jpg", str(max_dim), "high_res")
        if not os.path.exists(preview_path):
            logger.debug("create a preview imaage for the video")
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            ffmpeg.input(path).filter("scale", -2, max_dim).output(preview_path, map_metadata=0, threads=1, movflags="use_metadata_tags", vframes=1, loglevel="error").overwrite_output().run()
        image = Image.open(preview_path) 
    try:
        return send_image(image, False)
    finally:
        image.close()


@blueprint.route('/asset/setFacesAllIdentified/<int:asset_id>/<string:all_identified>', methods=['GET'])
def set_assert_all_faces_identified(asset_id, all_identified):
    asset = Asset.query.get(asset_id)
    asset.faces_all_identified = 'true' == all_identified
    db.session.commit()
    excludes=("-exif", "-gps", "-faces", "-things", "-section")
    return flask.jsonify(asset.to_dict(rules=excludes))


@blueprint.route('/asset/gps/<int:id>', methods=['GET'])
def get_gps(id):
    asset = Asset.query.get(id)
    if asset and asset.gps:
        return flask.jsonify(asset.gps.to_dict())
    return None


@blueprint.route('/asset/things/<int:id>', methods=['GET'])
def get_things_for_asset(id):
    asset = Asset.query.get(id)
    return jsonify_items(asset.things)


@blueprint.route('/asset/all/<int:page>/<int:size>', methods=['GET'])
def all_assets(page=0, size=30):
    q = Asset.query.order_by(Asset.created.desc())
    return jsonify_pagination(q, page, size)


@blueprint.route('/asset/data/<int:id>', methods=['GET'])
def asset_data(id):
    logger.debug("asset data")
    asset = Asset.query.get(id)
    return flask.jsonify(asset.to_dict())


@blueprint.route('/face/all', methods=['GET'])
def all_faces():
    logger.debug("all faces")
    face_ids = Face.query.with_entities(Face.id).all()
    return flask.jsonify(face_ids)


@blueprint.route('/asset/exif/<int:id>', methods=['GET'])
def exif_for_asset(id):
    logger.debug("Get exif %i", id)
    exif = {}
    for e in Asset.query.get(id).exif:
        if e.key in exif_filter:
            exif[e.key] = e.value
    return flask.jsonify(exif)


@blueprint.route('/asset/by_face/<int:id>', methods=['GET'])
def asset_by_face(id):
    logger.debug("asset for Face %i", id)
    asset = Face.query.get(id).asset
    return flask.jsonify(asset.to_dict())


def amend_query(request, q):
    fromDate = toDate = rating = None
    person_id = request.args.get("person_id")
    thing_id = request.args.get("thing_id")
    country = request.args.get("country")
    county = request.args.get("county")
    city = request.args.get("city")
    state = request.args.get("state")
    camera = request.args.get("camera")
    rating_s = request.args.get("rating")
    fromDate_s = request.args.get("from")
    toDate_s = request.args.get("to")
    album_id = request.args.get("album_id")

    if rating_s:
        rating = int(rating_s)
    if fromDate_s:
        fromDate = datetime.strptime(fromDate_s, "%Y-%m-%d")
    if toDate_s:
        toDate = datetime.strptime(toDate_s, "%Y-%m-%d")

    q = refine_query(q, person_id = person_id, thing_id = thing_id, country = country, county = county, 
                     city = city, state = state, camera = camera, rating = rating, fromDate = fromDate, toDate = toDate)

    if album_id:
        album = Album.query.get(album_id)
        if album.album_type != AlbumType.MANUAL:
            q = assets_from_smart_album(album, q)
        else:
            q = q.join(asset_album).filter(asset_album.c.album_id == album_id)
        logger.debug(q)
    return q


@blueprint.route('/section/all', methods=['GET'])
def all_sections():
    logger.debug("all sections")
    # compute_sections.delay()

    q = db.session.query(Section.id.label("id"),    
        db.func.count(Asset.id).label("num_assets")).join(Asset, Asset.section_id == Section.id).order_by(Section.id.asc())
    q = amend_query(request, q)

    sections = q.group_by(Section.id).all()
    sec_array = [{"id": n, "num_assets": m, "uuid":uuid.uuid1()} for n, m in sections]
    result = {}
    result['sections'] = sec_array

    # find first asset of first section
    # but check if we have sections at all (in the beginning no ...)
    most_recent_date = None
    oldest_date = None
    total_assets = 0
    if len(sec_array) > 0:
        sec_start_id = sec_array[0]['id']
        asset_recent = Asset.query.filter(
            Asset.section_id == sec_start_id).order_by(Asset.created.desc()).first()
        most_recent_date = asset_recent.created

        # and last/oldest asset of last section for the timeline
        sec_end_id = sec_array[-1]['id']
        oldest_asset = Asset.query.filter(and_(
            Asset.section_id == sec_end_id, Asset.created != None)).order_by(Asset.created.asc()).first()
        oldest_date = oldest_asset.created

        total = Asset.query.filter(Asset.ignore == False)
        total = amend_query(request, total)
        total_assets = total.count()

    result["max_date"] = most_recent_date
    result["min_date"] = oldest_date
    result["totalAssets"] = total_assets
    return flask.jsonify(result)


@blueprint.route('/section/find_by_date/<date_str>', methods=['GET'])
def get_section_by_date(date_str):
    logger.debug("section/find_by_date")
    date = datetime.strptime(date_str, "%Y-%m-%d")
    asset = Asset.query.filter(Asset.created < date).order_by(
        Asset.created.desc()).first()
    return flask.jsonify(asset.section.id)


@blueprint.route('/asset/importing', methods=['GET'])
def currently_importing():
    logger.debug("Get assets currently importing")

    assets = Asset.query.filter(and_(Asset.section == None, Asset.ignore == False))
    return list_as_json(
            assets, 
            excludes=("-exif", "-gps", "-faces", 
            "-things", "-section", "-albums"))


@blueprint.route('/asset/by_section/<int:id>', methods=['GET'])
def asset_by_section(id):
    logger.debug("Get section %i", id)

    q = Asset.query.filter(Asset.ignore == False)

    q = amend_query(request, q)
    assets = q.filter(Asset.section_id == id).order_by(Asset.created.desc())
    return list_as_json(
            assets, 
            excludes=("-exif", "-gps", "-faces", 
            "-things", "-section", "-albums"))


def face_assigned_by_human(face):
    face.distance_to_human_classified = 0
    face.confidence_level = Face.CLASSIFICATION_CONFIDENCE_LEVEL_CONFIRMED
    face.confidence = 0.0

@blueprint.route('/face/assign_face_to_person', methods=['POST'])
def assign_face_to_person():
    req_data = request.get_json()
    person_id = req_data.get("personId")
    name = req_data.get("name")
    face_id = req_data.get("faceId")
    person = Person.query.get(person_id)
    if not person:
        person = Person()
        person.name = name
        person.confirmed = True
        person.ignore = False

    logger.debug("Assign face %d to %d", face_id, person.id)
    face = Face.query.get(face_id)
    assign_new_person(face, person)
    face_assigned_by_human(face)

    db.session.commit()
    return flask.jsonify(True)


def set_name_faces(personId, newPersonId, name, face_ids):
    logger.debug("Set Face Name for %s", name)
    person = Person.query.get(personId)

    if (newPersonId is None):
        # This is a new person, so we need to set the name and remove all
        # faces which have not been confirmed by the user
        person.name = name
        person.confirmed = True
        to_be_removed = []
        for face in person.faces:
            if face.id not in face_ids:
                # face.person = None
                # person.faces.remove(face)
                to_be_removed.append(face.id)
            else:
                face_assigned_by_human(face)

        for to_be_removed_id in to_be_removed:
            face = Face.query.get(to_be_removed_id)
            person.faces.remove(face)
        # db.session.commit()

    else:
        # This is an existing person, so we need to do two things
        # move all selected faces to the identified person
        # discard the other person
        newPerson = Person.query.get(newPersonId)
        for fid in face_ids:
            face = Face.query.get(fid)
            face_assigned_by_human(face)
            face.person = newPerson

        # Now remove those faces that have not been confirmed bye the user and remove the person
        # therefore iterate over the person, remove the face relationship and delete the person
        for face in person.faces:
            face.person = None
            face.confidence_level = None
            face.distance_to_human_classified = None
            face.confidence = None

        db.session.delete(person)
    db.session.commit()


@blueprint.route('/face/setname', methods=['POST'])
def set_facename():

    req_data = request.get_json()
    logger.debug(req_data)
    # name = req_data["name"]
    ids = req_data["ids"]
    personId = req_data['oldPersonId']
    newPerson = req_data['newPerson']
    if isinstance(newPerson, dict):
        # Merge existing person and new Faces
        set_name_faces(personId, newPerson['id'], newPerson['name'], ids)
    else:
        # Completely new Person
        set_name_faces(personId, None, newPerson, ids)

    return flask.jsonify(True)


def _ignore_face(face):
    face.ignore = True
    face.person = None
    face.confidence_level = None
    face.distance_to_human_classified = 0


def _reset_face(face):
    face.ignore = False
    face.person = None
    face.confidence_level = None
    face.distance_to_human_classified = 0


@blueprint.route('/person/ignore_unknown_person/<int:person_id>', methods=['GET'])
def ignore_unknonw_person(person_id):
    person = Person.query.get(person_id)
    for face in person.faces:
        _ignore_face(face)
    db.session.delete(person)
    db.session.commit()
    return all_persons()


@blueprint.route('/person/forget/<int:person_id>', methods=['GET'])
def forget_person(person_id):
    logger.debug("Forgetting person %d", person_id)
    person = Person.query.get(person_id)
    # just ignore the person for the time being
    person.ignore = True
    #  and do the rest of the cleaning in the background as it can consume some time
    celery.send_task("timeline.tasks.match_tasks.reset_person", (person_id,), queue="beat", headers=dedup_header(person_id, "reset-person"))
    db.session.commit()

    #for face in person.faces:
    #    face.ignore = False
    #    face.person = None
    #    face.already_clustered = False
    #    face.confidence_level = None
    #   face.distance_to_human_classified = None
    #db.session.delete(person)

    return all_persons()


@blueprint.route('/person/merge/<int:src_person_id>/<int:target_person_id>', methods=['GET'])
def merge_persons(src_person_id, target_person_id):
    logger.debug("Merge faces from person %i to %i",
                 src_person_id, target_person_id)
    src_person = Person.query.get(src_person_id)
    target_person = Person.query.get(target_person_id)
    for face in src_person.faces:
        face.person = target_person
        face_assigned_by_human(face)
    db.session.delete(src_person)
    db.session.commit()
    return flask.jsonify(True)


@blueprint.route('/person/rename', methods=['POST'])
def rename_persons():
    req_data = request.get_json()
    personId = int(req_data['personId'])
    name = req_data['name']

    person = Person.query.get(personId)
    person.name = name
    if not person.confirmed:
        # we rename a not yet confirmed persons that are coming from the clustering
        # therefore all the related faces will be claaed as classified by human
        for face in person.faces:
            face_assigned_by_human(face)

        person.confirmed = True

    db.session.commit()
    return flask.jsonify(person.to_dict())


@blueprint.route('/person/all', methods=['GET'])
def all_persons():
    persons = Person.query.filter(Person.ignore != True).order_by(Person.name).all()
    return flask.jsonify([p.to_dict() for p in persons])


@blueprint.route('/person/known', methods=['GET'])
def known_persons():
    persons = Person.query.filter(
        and_(Person.confirmed == True, Person.ignore != True)).order_by(Person.name).all()
    return flask.jsonify([p.to_dict() for p in persons])


@blueprint.route('/person/<int:page>/<int:size>', methods=['GET'])
def persons(page, size):
    filters = [ Person.ignore != True ]
    person_id = request.args.get("filter.person_id")
    if person_id:
        filters.append( Person.id == person_id )
    person_name = request.args.get("filter.person_name")
    if person_name:
        filters.append( Person.name.contains(person_name) )
    paginate = Person.query.filter(and_(*filters)).order_by(Person.name)
    return jsonify_pagination(paginate, page, size)


@blueprint.route('/things/all', methods=['GET'])
def all_things():
    # things = Thing.query.order_by(Thing.label_en).all()
    things = Thing.query.filter(
        Thing.assets != None).order_by(Thing.label_en).all()
    return jsonify_items(things)


@blueprint.route('/things/preview_asset', methods=['GET'])
def thing_preview_asset():
    thing_id = request.args.get("thing_id")
    country = request.args.get("country")
    county = request.args.get("county")
    city = request.args.get("city")
    state = request.args.get("state")
    assets = None
    if thing_id:
        thing = Thing.query.get(thing_id)
        assets = thing.assets

    else:
        if country:
            assets = Asset.query.join(GPS).filter(
                GPS.country == country).order_by(GPS.country).all()
        elif county:
            assets = Asset.query.join(GPS).filter(
                GPS.county == county).order_by(GPS.county).all()
        elif city:
            assets = Asset.query.join(GPS).filter(
                GPS.city == city).order_by(GPS.city).all()
        elif state:
            assets = Asset.query.join(GPS).filter(
                GPS.state == state).order_by(GPS.state).all()

    assets_index = random.randrange(0, len(assets))
    asset = assets[assets_index]

    return flask.jsonify(asset.to_dict())


@blueprint.route('/face/data/by_person/<int:person_id>', methods=['GET'])
def faces_by_person(person_id):
    # get data only for faces we are really sure they belong to a person
    face = Face.query.join(Person).filter(
        or_(
            and_(Person.confirmed == True,  Face.person_id == person_id, Person.id == person_id, Face.confidence_level >= Face.CLASSIFICATION_CONFIDENCE_LEVEL_SAFE),
            and_(Person.confirmed == False, Face.person_id == person_id, Person.id == person_id)
        )
    ).first()
    # index = 0
    #index = request.args.get("index")
    # if not index:
    #    index = random.randrange(len(faces))
    return flask.jsonify(face.to_dict())


@blueprint.route('/asset/by_person/<int:person_id>/<int:page>/<int:size>', methods=['GET'])
def assets_by_person(person_id, page, size):
    paginate = Asset.query.join(Face, and_(Face.asset_id == Asset.id, Face.person_id == person_id)).order_by(
        Asset.created.desc())
    return jsonify_pagination(paginate, page, size)


@blueprint.route('/person/by_asset/<int:asset_id>', methods=['GET'])
def get_persons_by_asset(asset_id):
    persons = Person.query.join(Face, and_(
        Person.ignore != True, Face.asset_id == asset_id, Person.id == Face.person_id))
    return jsonify_items(persons)


@blueprint.route('/face/recent/<int:page>/<int:size>', methods=['GET'])
def faces_recent(page, size):
    logger.debug("get recent faces up to %i", size)
    filters = [ Face.updated.is_not(None), Face.person_id == Person.id ]
    person_id = request.args.get("filter.person_id")
    if person_id:
        filters.append( Face.person_id == person_id )
    person_name = request.args.get("filter.person_name")
    if person_name:
        filters.append( Person.name.contains(person_name) )
        
    if request.args.get("filter.switchNone") == 'false':
        filters.append( Face.confidence_level != Face.CLASSIFICATION_CONFIDENCE_NONE )
    if request.args.get("filter.switchMayBe") == 'false':
        filters.append( Face.confidence_level != Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE )
    if request.args.get("filter.switchSafe") == 'false':
        filters.append( Face.confidence_level != Face.CLASSIFICATION_CONFIDENCE_LEVEL_SAFE )
    if request.args.get("filter.switchVerySafe") == 'false':
        filters.append( Face.confidence_level != Face.CLASSIFICATION_CONFIDENCE_LEVEL_VERY_SAFE )
    if request.args.get("filter.switchConfirmed") == 'false':
        filters.append( Face.confidence_level != Face.CLASSIFICATION_CONFIDENCE_LEVEL_CONFIRMED )
      
    q = Face.query.join(Person).filter(and_(*filters)).order_by(Face.updated.desc())
    from timeline.util.db import show_query
    show_query(q)
    paginate = q.paginate(page=page, per_page=size, error_out=False)
    
    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])    
    known_faces = find_all_classified_known_faces(max_faces) # find_all_classified_faces()
    
    list = []
    for face in paginate.items:
        result = face.to_dict()
        asset = Asset.query.get(face.asset_id) 
        excludes=("-exif", "-gps", "-faces", "-things", "-section")
        result["photo"] = asset.to_dict(rules=excludes)

        if face.person_id:
            person = Person.query.get(face.person_id)
            result["person"] = person.to_dict()
            result["distance"] = -1
        else:
            if len(known_faces) > 0:
                id, distance = find_closest(face, known_faces)
                nearest = Face.query.get(id).person
                result["person"] =  nearest.to_dict()
                result["distance"] = distance.item()

        list.append(result)

    result = {
        "items": list,
        "pages": paginate.pages,
        "total": paginate.total
    }
    json = flask.jsonify(result)
    return json    


@blueprint.route('/face/by_asset/<int:asset_id>', methods=['GET'])
def get_faces_by_asset(asset_id):
    faces = Asset.query.get(asset_id).faces
    return jsonify_items(faces)


@blueprint.route('/face/ignore/<string:face_ids_str>', methods=['GET'])
def ignore_face(face_ids_str):
    face_ids = face_ids_str.split(",")
    for face_id in face_ids:
        if face_id:
            face = Face.query.get(face_id)
            _ignore_face(face)
    db.session.commit()
    return flask.jsonify(True)

@blueprint.route('/face/reset/<int:face_id>', methods=['GET'])
def reset_face(face_id):
    face = Face.query.get(face_id)
    _reset_face(face)
    db.session.commit()
    return flask.jsonify(True)


@blueprint.route('/face/allUnknownAndClosest/<int:page>/<int:size>', methods=['GET'])
def get_unknown_faces_and_closest(page, size):
    q = Face.query.filter(and_(
        Face.ignore == False,
        Face.person_id == None))
    logger.debug(q)
    paginate = q.paginate(page=page, per_page=size, error_out=False)
    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])
    known_faces = find_all_classified_known_faces(max_faces) # find_all_classified_faces()

    list = []
    for face in paginate.items:
        result = face.to_dict()
        if len(known_faces) > 0:
            id, distance = find_closest(face, known_faces)
            nearest = Face.query.get(id).person
            result["person"] = nearest.to_dict()
            result["distance"] = distance.item()
        asset = Asset.query.get(face.asset_id) 
        excludes=("-exif", "-gps", "-faces", "-things", "-section")
        result["photo"] = asset.to_dict(rules=excludes)
        list.append(result)

    result = {
        "items": list,
        "pages": paginate.pages,
        "total": paginate.total
    }
    json = flask.jsonify(result)
    return json


@blueprint.route('/face/facesToConfirm/<int:page>/<int:size>', methods=['GET'])
def get_faces_to_confirm(page, size):
    q = Face.query.filter(and_(
            Face.ignore == False,
            Face.person_id != None,
            Face.confidence_level == Face.CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE))
    logger.debug(q)
    paginate = q.paginate(page=page, per_page=size, error_out=False)
    list = []
    for face in paginate.items:
        result = face.to_dict()
        asset = Asset.query.get(face.asset_id) 
        excludes=("-exif", "-gps", "-faces", "-things", "-section")
        result["photo"] = asset.to_dict(rules=excludes)
        list.append(result)
    result = {
        "items": list,
        "pages": paginate.pages,
        "total": paginate.total
    }
    json = flask.jsonify(result)
    return json


@blueprint.route('/face/all_unknown/<int:page>/<int:size>', methods=['GET'])
def get_unknown_faces(page, size):
    q = Face.query.filter(and_(
        Face.ignore == False,
        Face.person_id == None))
    logger.debug(q)
    return jsonify_pagination(q, size=size, page=page)


@blueprint.route('/face/nearestKnownFaces/<int:face_id>', methods=['GET'])
def nearest_known_faces(face_id):
    logger.debug("Get nearest known faces for %d", face_id)
    face = Face.query.get(face_id)
    max_faces = int(current_app.config['FACE_CLUSTER_MAX_FACES'])

    known_faces = find_all_classified_known_faces(max_faces) # find_all_classified_faces()
    logger.debug("Get %d known faces to compare, now comparing", len(known_faces))
    result = {}
    if len(known_faces) > 0:
        id, distance = find_closest(face, known_faces)
        logger.debug("Comparison done")

        nearest = Face.query.get(id).person
        result = {"person": nearest.to_dict(), "distance": distance.item()}
    return flask.jsonify(result)


def de_tupelize(list_of_tupel):
    l = [v for v, in list_of_tupel]
    return flask.jsonify(l)


""" def amend_query_for_search_page(request, q):
    country = request.args.get("country")
    person_id = request.args.get("person_id")
    city = request.args.get("city")
    toDate = request.args.get("to")
    album_id = request.args.get("album_id")

    if person_id:
        q = q.join(Face, and_(and_(Face.person_id == person_id, Face.asset_id == asset.id)
    if country:
 """

@blueprint.route('/exif/camera_makes', methods=['GET'])
def exif_camera_makes():
    camera_makes = Exif.query.filter(
        Exif.key == 'Make').with_entities(Exif.value).distinct()
    # with_entities returns tupel, we are only interested in the first and only one, so get rid of the tupel
    return de_tupelize(camera_makes.all())

@blueprint.route('/location/countries', methods=['GET'])
def locations_country():
    countries = GPS.query.filter(
        GPS.country != None).with_entities(GPS.country).distinct()
    # with_entities returns tupel, we are only interested in the first and only one, so get rid of the tupel
    return de_tupelize(countries.all())


@blueprint.route('/location/cities', methods=['GET'])
def locations_city():
    cities = GPS.query.filter(
        GPS.city != None).with_entities(GPS.city).distinct()
    return de_tupelize(cities.all())


@blueprint.route('/location/counties', methods=['GET'])
def locations_county():
    counties = GPS.query.filter(
        GPS.county != None).with_entities(GPS.county).distinct()
    return de_tupelize(counties.all())


@blueprint.route('/location/states', methods=['GET'])
def locations_states():
    counties = GPS.query.filter(
        GPS.state != None).with_entities(GPS.state).distinct()
    return de_tupelize(counties.all())


def jsonify_items(items):
    return flask.jsonify([item.to_dict() for item in items])


@blueprint.route('/')
def index():
    return flask.render_template("index.html")


@blueprint.route('/time/scale', methods=['GET'])
def get_time_scale():
    qry = db.session.query(db.func.max(Asset.created).label("max"),
                           db.func.min(Asset.created).label("min"))
    res = qry.one()

    result = {"min": res.min, "max": res.max}
    return flask.jsonify(result)


@blueprint.route('/checkNewFaces', methods=['GET'])
def check_new_faces():
    status = Status.query.first()
    return flask.jsonify(status.new_faces)


@blueprint.route('/setFacesSeen', methods=['GET'])
def set_faces_seen():
    status = Status.query.first()
    status.new_faces = False
    db.session.commit()
    return flask.jsonify(True)


@blueprint.route('/deleteEmptyPersons', methods=['GET'])
def delete_empty_persons():
    Person.query.filter(~Person.faces.any()).delete(synchronize_session=False)
    db.session.commit()
    return flask.jsonify(True)


@blueprint.route('getTotalassetCount', methods=['GET'])
def total_assets():
    return flask.jsonify(Asset.query.count())


@blueprint.route('/matchAllUnknownFaces', methods=['GET'])
def match_all_unknown():
    match_all_unknown_faces.apply_async((True,), queue='match')
    # match_all_fast(force=True)
    return flask.jsonify(True)


@blueprint.route('/group_faces', methods=['GET'])
def group():
    group_faces.apply_async((True,), queue='match')
    # match_all_fast(force=True)
    return flask.jsonify(True)
