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

import os

import flask
from flask import Blueprint

from timeline.tasks.face_tasks import match_known_face, find_all_classified_faces, find_closest, match_all_unknown_faces, \
    group_faces
from timeline.util.image_ops import exif_transpose, read_and_transpose, resize_width
from sqlalchemy import and_, or_
import random
import logging
from timeline.domain import Photo, Face, Section, Status, Person, Thing, photo_thing, GPS
from timeline.extensions import db
from flask import request
from PIL import Image, ImageDraw
from timeline.api.photos import send_image
from timeline.util.path_util import get_full_path, get_preview_path
from datetime import datetime
from timeline.tasks.face_tasks import assign_new_person

blueprint = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

exif_filter = ["FocalLength", "ExifImageWidth", "ExifImageHeight", 
        "Make", "Model", "ExposureTime", "Copyright", "FNumber", "  ","LensModel", "Artist"]

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
    preview_path = get_preview_path(str(id) + ".png", "faces/" + str(dim))
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path)


@blueprint.route('/face/preview/<int:max_dim>/<int:id>.png', methods=['GET'])
def face_preview(id, max_dim=300):
    face = Face.query.get(id)
    if face:
        path = get_full_path(face.photo.path)
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
        path = get_full_path(face.photo.path)
        image = read_and_transpose(path)
        result = image.crop((face.x, face.y, face.x + face.w, face.y + face.h))
        return send_image(result, False, face.created)
    return flask.redirect('/404')


@blueprint.route('/face/by_person/<int:id>', methods=['GET'])
def face_by_person(id):
    # faces = Person.query.get(id).faces
    # faces = Face.query.filter(and_(Face.person_id == id, Face.confidence <= Face.DISTANCE_SAFE)).all()
    faces = Face.query.join(Person).filter(and_(Face.person_id == Person.id, Person.id == id, or_(Face.confidence <= Face.DISTANCE_SAFE, Person.confirmed == False))).all()
    return jsonify_items(faces)


@blueprint.route('/photo/preview/<int:max_dim>/<int:id>.jpg', methods=['GET'])
def photo_preview(id, max_dim):
    photo = Photo.query.get(id)
    if photo is None:
        return flask.redirect('/404')

    path = get_full_path(photo.path)
    image = read_and_transpose(path)
    size = resize_width(image, max_dim)
    image.thumbnail(size)

    return send_image(image, False)

@blueprint.route('/photo/gps/<int:id>', methods=['GET'])
def get_gps(id):
    photo = Photo.query.get(id)
    if photo and photo.gps:
        return flask.jsonify(photo.gps.to_dict())
    return None

@blueprint.route('/photo/things/<int:id>', methods=['GET'])
def get_things_for_photo(id):
    photo = Photo.query.get(id)
    return jsonify_items(photo.things);

@blueprint.route('/photo/all/<int:page>/<int:size>', methods=['GET'])
def all_photos(page=0, size=30):
    q = Photo.query.order_by(Photo.created.desc())
    return jsonify_pagination(q, page, size)


@blueprint.route('/photo/data/<int:id>', methods=['GET'])
def photo_data(id):
    logger.debug("photo data")
    photo = Photo.query.get(id)
    return flask.jsonify(photo.to_dict())


@blueprint.route('/face/all', methods=['GET'])
def all_faces():
    logger.debug("all faces")
    face_ids = Face.query.with_entities(Face.id).all()
    return flask.jsonify(face_ids)

@blueprint.route('/photo/exif/<int:id>', methods=['GET'])
def exif_for_photo(id):
    logger.debug("Get exif %i", id)
    exif = {}
    for e in Photo.query.get(id).exif:
        if e.key in exif_filter:
            exif[e.key] = e.value
    return flask.jsonify(exif);

@blueprint.route('/photo/by_face/<int:id>', methods=['GET'])
def photo_by_face(id):
    logger.debug("Photo for Face %i", id)
    photo = Face.query.get(id).photo
    return flask.jsonify(photo.to_dict())


def list_as_json(list, excludes=None):
    return flask.jsonify([element.to_dict(rules=excludes) for element in list])

def amend_query(request, q):
    person_id = request.args.get("person_id")
    thing_id = request.args.get("thing_id")
    country = request.args.get("country")
    county = request.args.get("county")
    city = request.args.get("city")
    state = request.args.get("state")

    if person_id:
        q = q.join(Face, and_(Face.person_id == person_id, Face.photo_id == Photo.id))
    if thing_id:
        q = q.join(photo_thing, and_(photo_thing.c.photo_id == Photo.id, photo_thing.c.thing_id == thing_id))
    if city:
        q = q.join(GPS).filter(GPS.city == city)
    if county:
        q = q.join(GPS).filter(GPS.county == county)
    if country:
        q = q.join(GPS).filter(GPS.country == country)
    if state:
        q = q.join(GPS).filter(GPS.state == state)

    return q


@blueprint.route('/section/all', methods=['GET'])
def all_sections():
    logger.debug("all sections")
    # compute_sections.delay()

    q = db.session.query(Section.id.label("id"), db.func.count(Photo.id).label("num_photos")).join(Photo,
                                                                        Photo.section_id == Section.id)
    q = amend_query(request, q)

    sections = q.group_by(Section.id).all()
    sec_array = [{"id": n, "num_photos": m} for n, m in sections]
    result = {}
    result['sections'] = sec_array

    # find first photo of first section
    # but check if we have sections at all (in the beginning no ...)
    most_recent_date = None
    oldest_date = None
    total_photos = 0
    if len(sec_array) > 0:
        sec_start_id = sec_array[0]['id']
        photo_recent = Photo.query.filter(Photo.section_id == sec_start_id).order_by(Photo.created.desc()).first()
        most_recent_date = photo_recent.created;

        # and last/oldest photo of last section for the timeline
        sec_end_id = sec_array[-1]['id']
        oldest_photo = Photo.query.filter(and_(Photo.section_id == sec_end_id, Photo.created != None)).order_by(Photo.created.asc()).first()
        oldest_date = oldest_photo.created

        total = Photo.query
        total = amend_query(request, total)
        total_photos = total.count()

    result["max_date"] = most_recent_date
    result["min_date"] = oldest_date
    result["totalPhotos"] = total_photos
    return flask.jsonify(result)


@blueprint.route('/section/find_by_date/<date_str>', methods=['GET'])
def get_section_by_date(date_str):
    logger.debug("section/find_by_date")
    date = datetime.strptime(date_str, "%Y-%m-%d")
    photo = Photo.query.filter(Photo.created < date).order_by(Photo.created.desc()).first()
    return flask.jsonify(photo.section.id)


@blueprint.route('/photo/by_section/<int:id>', methods=['GET'])
def photo_by_section(id):
    logger.debug("Get section %i", id)

    q = Photo.query

    q = amend_query(request, q)
    photos = q.filter(Photo.section_id == id).order_by(Photo.created.desc())
    return list_as_json(photos, excludes=("-exif", "-gps", "-faces", "-things", "-section"))
    # return flask.jsonify(photos.all())


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

    face = Face.query.get(face_id)
    assign_new_person(face, person)
    face.distance_to_human_classified = 0
    face.classified_by = Face.HUMAN
    
    db.session.commit()
    # return flask.jsonify(face.to_dict())
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
                face.classified_by = Face.HUMAN
                face.distance_to_human_classified = 0

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
            face.classified_by = Face.HUMAN
            face.distance_to_human_classified = 0
            face.person = newPerson

        # Now remove those faces that have not been confirmed bye the user and remove the person
        # therefore iterate over the person, remove the face relationship and delete the person
        for face in person.faces:
            face.person = None
            face.classified_by = None
            face.distance_to_human_classified = None

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

    # after we add new names we need to match the unknown faces against the new face
    #for face_id in ids:
    #    match_known_face.apply_async((face_id,), queue='match')

    return flask.jsonify(True)

@blueprint.route('/person/ignore_unknown_person/<int:person_id>', methods=['GET'])
def ignore_unknonw_person(person_id):
    person = Person.query.get(person_id)
    for face in person.faces:
        face.ignore = True
        face.person = None
    db.session.delete(person)
    db.session.commit()
    return all_persons()

@blueprint.route('/person/forget/<int:person_id>', methods=['GET'])
def forget_person(person_id):
    person = Person.query.get(person_id)
    for face in person.faces:
        face.ignore = False
        face.person = None
        face.already_clustered = False
    db.session.delete(person)
    db.session.commit()
    return all_persons()

@blueprint.route('/person/merge/<int:src_person_id>/<int:target_person_id>', methods=['GET'])
def merge_persons(src_person_id, target_person_id):
    logger.debug("Merge faces from person %i to %i", src_person_id, target_person_id)
    src_person = Person.query.get(src_person_id)
    target_person = Person.query.get(target_person_id)
    for face in src_person.faces:
        face.person = target_person
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
    person.confirmed = True
    db.session.commit()
    return flask.jsonify(person.to_dict())


@blueprint.route('/person/all', methods=['GET'])
def all_persons():
    persons = Person.query.order_by(Person.name).all()
    return flask.jsonify([p.to_dict() for p in persons])

@blueprint.route('/person/known', methods=['GET'])
def known_persons():
    persons = Person.query.filter(Person.confirmed == True).order_by(Person.name).all()
    return flask.jsonify([p.to_dict() for p in persons])


@blueprint.route('/things/all', methods=['GET'])
def all_things():
    # things = Thing.query.order_by(Thing.label_en).all()
    things = Thing.query.filter(Thing.photos != None).order_by(Thing.label_en).all()
    return jsonify_items(things)


@blueprint.route('/things/preview_photo', methods=['GET'])
def thing_preview_photo():
    thing_id = request.args.get("thing_id")
    country = request.args.get("country")
    county = request.args.get("county")
    city = request.args.get("city")
    state = request.args.get("state")
    photos = None
    if thing_id:
        thing = Thing.query.get(thing_id)
        photos = thing.photos

    else:
        if country:
            photos = Photo.query.join(GPS).filter(GPS.country == country).order_by(GPS.country).all()
        elif county:
            photos = Photo.query.join(GPS).filter(GPS.county == county).order_by(GPS.county).all()
        elif city:
            photos = Photo.query.join(GPS).filter(GPS.city == city).order_by(GPS.city).all()
        elif state:
            photos = Photo.query.join(GPS).filter(GPS.state == state).order_by(GPS.state).all()

    photos_index = random.randrange(0, len(photos))
    photo = photos[photos_index]

    return flask.jsonify(photo.to_dict())


def jsonify_pagination(q, page, size):
    paginate = q.paginate(page=page, per_page=size, error_out=False)
    result = {
        "items": [item.to_dict() for item in paginate.items],
        "pages": paginate.pages,
        "total": paginate.total
    }
    json = flask.jsonify(result)
    return json


@blueprint.route('/face/data/by_person/<int:person_id>', methods=['GET'])
def faces_by_person(person_id):
    faces = Person.query.get(person_id).faces
    index = 0
    #index = request.args.get("index")
    #if not index:
    #    index = random.randrange(len(faces))
    return flask.jsonify(faces[index].to_dict())


@blueprint.route('/photo/by_person/<int:person_id>/<int:page>/<int:size>', methods=['GET'])
def photos_by_person(person_id, page, size):
    paginate = Photo.query.join(Face, and_(Face.photo_id == Photo.id, Face.person_id == person_id)).order_by(
        Photo.created.desc())
    return jsonify_pagination(paginate, page, size)


@blueprint.route('/person/by_photo/<int:photo_id>', methods=['GET'])
def get_persons_by_photo(photo_id):
    persons = Person.query.join(Face, and_(Face.photo_id == photo_id, Person.id == Face.person_id))
    return jsonify_items(persons)


@blueprint.route('/face/by_photo/<int:photo_id>', methods=['GET'])
def get_faces_by_photo(photo_id):
    faces = Photo.query.get(photo_id).faces
    return jsonify_items(faces)


def de_tupelize(list_of_tupel):
    l = [v for v, in list_of_tupel]
    return flask.jsonify(l)

@blueprint.route('/location/countries', methods=['GET'])
def locations_country():
    countries = GPS.query.filter(GPS.country != None).with_entities(GPS.country).distinct()
    # with_entities return tupel, we are only interested in the first and only one, so get rid of the tupel
    return de_tupelize(countries.all())

@blueprint.route('/location/cities', methods=['GET'])
def locations_city():
    cities = GPS.query.filter(GPS.city != None).with_entities(GPS.city).distinct()
    return de_tupelize(cities.all())

@blueprint.route('/location/counties', methods=['GET'])
def locations_county():
    counties = GPS.query.filter(GPS.county != None).with_entities(GPS.county).distinct()
    return de_tupelize(counties.all())

@blueprint.route('/location/states', methods=['GET'])
def locations_states():
    counties = GPS.query.filter(GPS.state != None).with_entities(GPS.state).distinct()
    return de_tupelize(counties.all())

def jsonify_items(items):
    return flask.jsonify([item.to_dict() for item in items])


@blueprint.route('/')
def index():
    return flask.render_template("index.html")


@blueprint.route('/time/scale', methods=['GET'])
def get_time_scale():
    qry = db.session.query(db.func.max(Photo.created).label("max"),
                        db.func.min(Photo.created).label("min"))
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

@blueprint.route('getTotalPhotoCount', methods=['GET'])
def total_photos():
    return flask.jsonify(Photo.query.count())


@blueprint.route('/nearestKnowFaces/<int:face_id>', methods=['GET'])
def nearest_known_faces(face_id):
    face = Face.query.get(face_id)
    known_faces = find_all_classified_faces()
    id, distance = find_closest(face, known_faces)
    return flask.jsonify((id, distance.item()))


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


