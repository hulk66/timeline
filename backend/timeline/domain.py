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

from enum import unique
import pickle
import zlib
from sqlalchemy_serializer import SerializerMixin
import sqlalchemy
from timeline.extensions import db


class NumpyType(sqlalchemy.types.TypeDecorator):
    cache_ok = True
    impl = sqlalchemy.types.LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            return zlib.compress(value.dumps())

    def process_result_value(self, value, dialect):
        if value is not None:
            return pickle.loads(zlib.decompress(value))


class Person(db.Model, SerializerMixin):
    __tablename__ = 'persons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    faces = db.relationship("Face", back_populates="person")
    confirmed = db.Column(db.Boolean)
    ignore = db.Column(db.Boolean, index = True)
    serialize_rules = ('-faces',)


class Face(db.Model, SerializerMixin):
    __tablename__ = 'faces'

    CLASSIFICATION_CONFIDENCE_LEVEL_CONFIRMED = 4
    CLASSIFICATION_CONFIDENCE_LEVEL_VERY_SAFE = 3
    CLASSIFICATION_CONFIDENCE_LEVEL_SAFE = 2
    CLASSIFICATION_CONFIDENCE_LEVEL_MAYBE = 1
    CLASSIFICATION_CONFIDENCE_NONE = 0

    id = db.Column(db.Integer, primary_key=True)

    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'))
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'))
    encoding = db.Column(NumpyType)
    confidence_level = db.Column(db.Integer)
    already_clustered = db.Column(db.Boolean)

    distance_to_human_classified = db.Column(db.Integer, index=True)
    created = db.Column(db.DateTime)
    ignore = db.Column(db.Boolean, index=True)

    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    w = db.Column(db.Integer)
    h = db.Column(db.Integer)
    confidence = db.Column(db.Float)

    person = db.relationship("Person", back_populates="faces")
    photo = db.relationship("Photo", back_populates="faces")

    emotion = db.Column(db.String(20))
    emotion_confidence = db.Column(db.Float)

    predicted_age = db.Column(db.Integer) 
    predicted_gender = db.Column(db.String(10))
       
    serialize_rules = ('-encoding', '-photo')


photo_album = db.Table('photo_album', db.Model.metadata,
                       db.Column('photo_id', db.ForeignKey(
                           'photos.id'), primary_key=True),
                       db.Column('album_id', db.ForeignKey(
                           'albums.id'), primary_key=True)
                       )


class Album(db.Model, SerializerMixin):
    __tablename__ = 'albums'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    photos = db.relationship(
        'Photo', secondary=photo_album, back_populates='albums')

    smart = db.Column(db.Boolean)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer)
    person_id = db.Column(db.Integer)
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    county = db.Column(db.String(100))
    village = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    camera_make = db.Column(db.String(100))
    thing_id = db.Column(db.String(100))

    serialize_rules = ('-photos',)


""" class SmartAlbumCriteria(db.Model, SerializerMixin):
    __tablename__ = 'smartalbum_criteria'

    id = db.Column(db.Integer, primary_key=True)

    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer)
    person_id = db.Column(db.Integer)
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    county = db.Column(db.String(100))
    village = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    camera_make = db.Column(db.String(100))
    thing_id = db.Column(db.String(100))

    smart_album_id = db.Column(db.Integer, db.ForeignKey('smartalbum.id'))
    smart_album = db.relationship("SmartAlbum", back_populates="criterias")
    serialize_rules = ('-smart_album',)
 """

""" class SmartAlbum(db.Model, SerializerMixin):
    __tablename__ = 'smartalbum'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer)
    person_id = db.Column(db.Integer)
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    county = db.Column(db.String(100))
    village = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    camera_make = db.Column(db.String(100))
    thing_id = db.Column(db.String(100))

    # criterias = db.relationship("SmartAlbumCriteria", cascade="all, delete, delete-orphan")
 """


photo_thing = db.Table('photo_thing', db.Model.metadata,
                       db.Column('photo_id', db.ForeignKey(
                           'photos.id'), primary_key=True),
                       db.Column('thing_id', db.ForeignKey(
                           'things.id'), primary_key=True)
                       )


class Thing(db.Model, SerializerMixin):
    __tablename__ = 'things'
    # id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(50), primary_key=True)
    label_en = db.Column(db.String(100))  # ) , unique=True)

    photos = db.relationship(
        'Photo', secondary=photo_thing, back_populates='things')
    parent = db.relationship("Thing", uselist=False,
                             cascade="all, delete, delete-orphan")
    parent_id = db.Column(db.String(50), db.ForeignKey('things.id'))

    serialize_rules = ('-photos',)


class Photo(db.Model, SerializerMixin):
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(512), unique=True)
    filename = db.Column(db.String(100))
    directory = db.Column(db.String(512))
    ignore = db.Column(db.Boolean, index=True)
    faces = db.relationship("Face", back_populates="photo",
                            cascade="all, delete, delete-orphan")
    exif = db.relationship("Exif", cascade="all, delete, delete-orphan")
    added = db.Column(db.DateTime, index=True)
    created = db.Column(db.DateTime, index=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    stars = db.Column(db.Integer)
    score_aesthetic = db.Column(db.Float)
    score_technical = db.Column(db.Float)
    # score_brisque = db.Column(db.Float)

    gps = db.relationship(
        "GPS", uselist=False, cascade="all, delete, delete-orphan", 
        single_parent=True)
    gps_id = db.Column(db.Integer, db.ForeignKey('gps.id'))

    things = db.relationship(
        'Thing', secondary=photo_thing, back_populates='photos')
    albums = db.relationship(
        'Album', secondary=photo_album, back_populates='photos')

    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    section = db.relationship("Section", back_populates="photos")
    no_creation_date = db.Column(db.Boolean)

    serialize_rules = ('-faces',)

    def __repr__(self):
        return "<Photo(filename='%s', )>" % (
            self.filename)

    def rel_path(self):
        return

class DateRange(db.Model, SerializerMixin):
    __tablename__ = 'date_range'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_date = db.Column(db.DateTime, unique = True)
    # end_date = db.Column(db.DateTime, unique = True)


class Section(db.Model, SerializerMixin):
    __tablename__ = 'section'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dirty = db.Column(db.Boolean)
    photos = db.relationship("Photo")
    # num_photos = db.Column(db.Integer)
    oldest_date = db.Column(db.DateTime, unique = True)
    newest_date = db.Column(db.DateTime, unique = True)
    serialize_rules = ('-photos',)

# class Sec(db.Model, SerializerMixin):
#    __tablename__ = 'sec'
#
#    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
#
#    dirty = db.Column(db.Boolean)
#    start_date = db.Column(db.DateTime)
#    end_date = db.Column(db.DateTime)


class Status(db.Model, SerializerMixin):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    sections_dirty = db.Column(db.Boolean)
    new_faces = db.Column(db.Boolean)
    next_import_is_new = db.Column(db.Boolean)

    last_import_album = db.relationship(
        "Album", uselist=False, cascade="all, delete, delete-orphan", 
        single_parent=True)
    last_import_album_id = db.Column(db.Integer, db.ForeignKey('albums.id'))   
    in_sectioning = db.Column(db.Boolean)

class Exif(db.Model, SerializerMixin):
    __tablename__ = 'exif'
    # id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100),primary_key=True)
    value = db.Column(db.String(100))
    # label = db.Column(db.String(50))
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), primary_key=True)

    def __repr__(self):
        return "<Exif(Key='%s', Value='%s')>" % (
            self.key, self.value)


class GPS(db.Model, SerializerMixin):
    __tablename__ = 'gps'

    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    city = db.Column(db.String(100))
    road = db.Column(db.String(100))
    country_code = db.Column(db.String(10))
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postcode = db.Column(db.String(20))
    county = db.Column(db.String(100))
    village = db.Column(db.String(100))
    municipality = db.Column(db.String(100))
    display_address = db.Column(db.String(1000))
