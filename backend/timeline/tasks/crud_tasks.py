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

import logging
import os
import os.path
from datetime import datetime, timedelta
from pathlib import Path

from celery import chain
from flask import current_app
from PIL import Image, UnidentifiedImageError
from sqlalchemy.util.compat import u
from timeline.domain import Album, GPS, Exif, Person, Photo, Section, Status, DateRange
from timeline.extensions import celery, db
from timeline.util.gps import (get_exif_value, get_geotagging, get_gps_data,
                               get_labeled_exif, get_lat_lon)
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import (get_full_path, get_preview_path,
                                     get_rel_path)
from sqlalchemy import and_

logger = logging.getLogger(__name__)


def get_size(image):
    # return width and height considering a rotation
    exif = image.getexif()
    orientation = exif.get(0x0112)
    method = {
        2: Image.FLIP_LEFT_RIGHT,
        3: Image.ROTATE_180,
        4: Image.FLIP_TOP_BOTTOM,
        5: Image.TRANSPOSE,
        6: Image.ROTATE_270,
        7: Image.TRANSVERSE,
        8: Image.ROTATE_90,
    }.get(orientation)
    if method == Image.ROTATE_270 or method == Image.ROTATE_90:
        return image.size[1], image.size[0]
    return image.size


def create_photo(path, commit=True):
    logger.debug("Reading Photo %s", path)
    if not Path(path).exists():
        logger.warning("File does not exist: %s", path)
        return None

    img_path = get_rel_path(path)

    photo = Photo.query.filter(Photo.path == img_path).first()
    if photo:
        logger.info("Photo already exists %s. Skipping", img_path)
        return None

    try:
        image = Image.open(path)
    except UnidentifiedImageError:
        logger.error("Invalid Image Format for %s", path)
        return None
    except FileNotFoundError:
        logger.error("File not found: %s")
        return None

    photo = Photo()
    photo.added = datetime.today()
    photo.ignore = False
    photo.exif = []
    photo.path = img_path
    photo.directory, photo.filename = os.path.split(img_path)
    # photo.directory = os.path.
    photo.width, photo.height = get_size(image)  # image.size
    _extract_exif_data(photo, image)
    db.session.add(photo)
    # sort_photo_into_date_range(photo, commit = False)
    add_to_last_import(photo)

    if commit:
        db.session.commit()
    return photo.id


@celery.task(name = "Extract Exif Data for all Photos")
def extract_exif_all_photos(overwrite):
    for photo in Photo.query:
        extract_exif_data.apply_async((photo.id, overwrite), queue = 'process')

@celery.task(name = "Extract Exif")
def extract_exif_data(photo_id, overwrite):
    photo = Photo.query.get(photo_id)
    if not photo:
        logger.warning("Photo with ID %d does not exist", photo_id)
        return
    if overwrite or not photo.exif:    
        _extract_exif_data(photo)
    db.session.commit()


def _extract_exif_data(photo, image = None):

    logger.debug("Extract Exif Data for Photo %s", photo.path)
    if not image:
        path = get_full_path(photo.path)

        try:
            image = Image.open(path)
        except UnidentifiedImageError:
            logger.error("Invalid Image Format for %s", path)
            return None
        except FileNotFoundError:
            logger.error("File not found: %s")
            return None

    exif_raw = image.getexif()
    exif_data = get_labeled_exif(exif_raw)
    geotags = get_geotagging(exif_raw)
    gps_data = get_lat_lon(geotags)
    if gps_data:
        gps = GPS()
        photo.gps = gps
        photo.gps.latitude, photo.gps.longitude = gps_data

    photo.exif = []
    for key in exif_data.keys():
        raw_value = exif_data[key]
        try:
            value = get_exif_value(key, raw_value)
            if value is not None:
                exif = Exif()
                photo.exif.append(exif)

                exif.key, exif.value = key, str(value)

        except UnicodeDecodeError:
            logger.error("%s", img_path)

        # User either DateTimeOriginal or not available any other DateTime
        if key == 'DateTimeOriginal' or (key.startswith("DateTime") and photo.created is None):
            try:
                # set photo date
                dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                photo.created = dt
                photo.no_creation_date = False
            except ValueError:
                logger.error("%s can not be parsed as Date for %s",
                             str(value), photo.path)

    if not photo.created:
        # there is either no exif date or it can't be parsed for the photo date, so we assumme it is old
        photo.created = datetime.today()
        photo.no_creation_date = True
        # they will be moved to the end later


def add_to_last_import(photo):
    status = Status.query.first()
    status.sections_dirty = True
    album = Album.query.get(status.last_import_album_id)

    if album is None:
        album = Album()
        album.name ="Last Import"
        db.session.add(album)
        status.last_import_album_id = album.id
        
    if status.next_import_is_new:
        album.photos = []
        status.next_import_is_new = False

    album.photos.append(photo)

# def update_sections(photo):
#
#    sec = Sec.query.find( and_(Sec.start_date <= photo.created, photo.created < Sec.end_date)).first()
#    if sec:
#        if size(sec) > MAX_SEC_SIZE:
#
#        else:
#            # all good, nothing to do


@celery.task(mame="Delete Photo")
def delete_photo(img_path, commit=True):
    logger.debug("Delete Photo %s", img_path)
    path = get_rel_path(img_path)
    for p in Photo.query.filter(Photo.path == path):
        # for face in p.faces:
        #    if (face.person is None):
        #        db.session.delete(face)
        # todo: remove preview also
        db.session.delete(p)

    for person in Person.query.filter(Person.faces == None):
        db.session.delete(person)

    Status.query.first().sections_dirty = True
    if commit:
        db.session.commit()


@celery.task(mame="Modify Photo")
def modify_photo(img_path):
    logger.debug("Modify Photo %s", img_path)

    delete_photo(img_path, commit=False)
    create_photo(img_path, commit=False)
    db.session.commit()


@celery.task(name="Move Photo")
def move_photo(img_path_src, img_path_dest):
    logger.debug("Move Photo from %s to %s", img_path_src, img_path_dest)
    path = get_rel_path(img_path_src)
    photos = Photo.query.filter(Photo.path == path).all()

    if len(photos) > 0:
        photos[0].path = get_rel_path(img_path_dest)
    Status.query.first().sections_dirty = True
    db.session.commit()

def sort_photo_into_date_range_task(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        logger.error("Something is wrong. Photo with id %i not found. Deleted already?")
        return
    sort_photo_into_date_range(photo, commit = True)


def find_date_range(photo: Photo) -> DateRange:
    date_range = DateRange.query.filter( photo.created >= DateRange.start_date).order_by(DateRange.start_date.desc()).with_for_update().first()
    if not date_range:
        date_range = DateRange()
        date_range.start_date = photo.created.date()
        db.session.add(date_range)
        db.session.commit()
    return date_range


def find_date_range2(photo: Photo) -> DateRange:
    date_range = DateRange.query.filter( and_(DateRange.end_date > photo.created, photo.created >= DateRange.start_date)).first()

    if not date_range:
        # no specific date range was found
        # so try to find one bloew or up

        date_range = DateRange.query.filter( DateRange.end_date > photo.created).order_by(DateRange.end_date.asc()).first()

        if not date_range:
            date_range = DateRange.query.filter( photo.created >= DateRange.start_date).order_by(DateRange.start_date.desc()).first()

            if not date_range:
                date_range = DateRange()
                date_range.start_date = photo.created
                date_range.end_date = date_range.start_date + timedelta(days = 1)
                db.session.add(date_range)
    
    if photo.created >= date_range.end_date:
        date_range.end_date = photo.created
    if photo.created < date_range.start_date:
        date_range.start_date = photo.created
    return date_range

def find_upper_start_date(date_range: DateRange) -> DateRange:
    upper_date_range = DateRange.query.filter( DateRange.start_date > date_range.start_date).order_by(DateRange.start_date.desc()).first()
    if not upper_date_range:
        upper_date_range = DateRange()
        #  = date_range.start_date.date() +  timedelta(days = 1)
        upper_date_range.start_date = date_to_datetime(datetime.today().date())
        db.session.add(upper_date_range)
    return upper_date_range

def date_to_datetime(d: datetime.date):
    return datetime(year = d.year, month = d.month, day = d.day)

def split_date_range(date_range: DateRange):
    upper_date_range = find_upper_start_date(date_range)
    if upper_date_range:

        delta = upper_date_range.start_date - date_range.start_date
        if delta.days > 1:
            # Only split it if the data range is more than just one day
            # if we exceeed the number of photos in one day then we just accept it
            new_date_range = DateRange()
            new_date_range.start_date = upper_date_range.start_date - timedelta(days = int(delta.days / 2))
            db.session.add(new_date_range)

def level_date_ranges(start_photo: Photo = None):
    logger.debug("Level data ranges for sectioning")

    status = Status.query.first()

    if not status.sections_dirty and Photo.query.filter(Photo.section == None).count() == 0:
        logger.debug("Level Date Ranges- nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return
        
    if not start_photo:
        start_photo = Photo.query.order_by(Photo.created.asc()).first()

    lower_date_range = DateRange.query.filter( start_photo.created >= DateRange.start_date).order_by(DateRange.start_date.desc()).first()
    if not lower_date_range:
        lower_date_range = DateRange()
        lower_date_range.start_date = date_to_datetime(start_photo.created.date())
        db.session.add(lower_date_range)

    upper_date_range = find_upper_start_date(lower_date_range)
    photos = Photo.query.filter( and_(upper_date_range.start_date > Photo.created, Photo.created >= lower_date_range.start_date ))

    if photos.count() < 300:
        # continue here 
        pass
    if DateRange.query.count() == 0:
        # create initial DateRange
        date_range = DateRange()


def sort_photo_into_date_range(photo, commit = True):
    logger.debug("Insert Photo into Section Range for %s", photo.path)
    
    date_range = find_date_range(photo)
    photos_in_range = Photo.query.filter( Photo.created >= date_range.start_date )

    if photos_in_range.count() > 300:
        split_date_range(date_range)
    elif photos_in_range.count() == 0:
        db.session.remove(date_range)
    else:
        if photo.created < date_range.start_date:
            date_range.start_date = photo.created
    if commit:
        db.session.commit()

    
    
@celery.task(name="Sort old Photos to end")
def sort_old_photos():
    logger.debug("Sort undated Photos")
    status = Status.query.first()
    if not status.sections_dirty:
        logger.debug("sort_old_photos - nothing to do")
        return

    oldest_photo = Photo.query.filter(
        Photo.ignore == False).order_by(Photo.created.asc()).first()
    if not oldest_photo:
        return
    min_date = oldest_photo.created - timedelta(days=1)
    photos = Photo.query.filter(Photo.no_creation_date == True)

    for photo in photos:
        # logger.debug("photo %i", photo.id)
        # logger.debug(min_date)
        photo.created = min_date
        min_date -= timedelta(seconds=1)

    db.session.commit()


def new_import():
    album = Album.query.get(0)
    if album is None:
        album = Album()
        album.id = 0
        album.name = 'Last Import'
    album.photos = []

    
@celery.task(ignore_result=True)
def compute_sections():
    logger.debug("Sectioning Photos")

    status = Status.query.first()

    if not status.sections_dirty and Photo.query.filter(Photo.section == None).count() == 0:
        logger.debug("Sectioning Photos - nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return
    sort_old_photos()

    batch_size = 200
    current_section = 0

    # Get all photos sorted descending, meaning the newest first
    photos = Photo.query.filter(Photo.ignore == False).order_by(
        Photo.created.desc()).limit(batch_size).all()
    while len(photos) > 0:
        # get the date of the oldest photo of that batch
        oldest_photo = photos[-1]
        # Find all photos that are on the same day as the oldest photo
        oldest_photo_prev_day = date_to_datetime(oldest_photo.created.date() - timedelta(days = 1))
        # now find all photos that a older as the oldest photo from batch but newer as the next day
        same_day_photos = Photo.query.filter( and_(Photo.ignore == False, Photo.created < oldest_photo.created, Photo.created > oldest_photo_prev_day)).all()

        # these photos will be added to the same section, so that each setion always start with a new day
        logger.debug("Sectioning %i photos", len(photos) + len(same_day_photos))
        section = Section.query.get(current_section)
        if not section:
            logger.debug("Creating new Section")
            section = Section()
            db.session.add(section)
            section.id = current_section

        #Photo.query.filter( and_(Photo.ignore == False, Photo.created > oldest_photo.created, Photo.created < oldest_photo_prev_day)).update( {Photo.section: section}, synchronize_session=False)

        for photo in photos:
            photo.section = section
        for photo in same_day_photos:
            photo.section = section
    
        photos = Photo.query \
            .filter(and_(Photo.ignore == False, Photo.created <= oldest_photo_prev_day)) \
            .order_by(Photo.created.desc()).limit(batch_size).all()
        current_section += 1
    
    Section.query.filter(Section.id >= current_section).delete()
    db.session.commit()
    logger.debug("Sectioning done")


def compute_sections_old():
    logger.debug("Compute Sections")
    status = Status.query.first()

    if not status.sections_dirty and Photo.query.filter(Photo.section == None).count() == 0:
        logger.debug("compute_sections - nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return

    sort_old_photos()

    offset = 0
    batch_size = 200
    current_section = 0
    photos = Photo.query.filter(Photo.ignore == False).order_by(
        Photo.created.desc()).limit(batch_size).all()
    prev_batch_date = None
    last_batch_date = None
    section = None
    initial = True

    while len(photos) > 0:
        logger.debug("Sectioning next batch %i with %i initial photos",
                     current_section, len(photos))
        photos_from_prev_batch = 0
        add_limit = 0
        new_batch = True
        for photo in photos:
            if initial or (new_batch and last_batch_date and last_batch_date.date() != photo.created.date()):
                initial = False
                if section:
                    section.num_photos = len(section.photos)
                    logger.debug(
                        "Compute Sections - Closing Section with %i photos", section.num_photos)
                    section.start_date = None
                add_limit = photos_from_prev_batch
                section = Section.query.get(current_section)
                if not section:
                    logger.debug("Creating new Section")
                    section = Section()
                    db.session.add(section)
                    section.id = current_section

                current_section += 1
                new_batch = False
            else:
                photos_from_prev_batch += 1
            offset += 1
            photo.section = section

        last_batch_date = photos[-1].created
        if prev_batch_date == last_batch_date:
            # make sure to always have a date break in the set of photos
            # otherwise we might come into an endless loop
            # let's see if this solves this strange problem
            last_batch_date -= timedelta(seconds=1)
        prev_batch_date = last_batch_date
        photos = Photo.query \
            .filter(Photo.created < last_batch_date) \
            .order_by(Photo.created.desc()).limit(batch_size + add_limit).all()

    status.sections_dirty = False
    db.session.commit()
    logger.debug("Compute Sections - Done")


@celery.task(ignore_result=True)
def schedule_next_compute_sections(minutes=None):
    if minutes:
        compute_sections_schedule = minutes
    else:
        compute_sections_schedule = int(
            current_app.config['COMPUTE_SECTIONS_EVERY_MINUTES'])
    logger.debug("Scheduling next computing section in %i minutes",
                 compute_sections_schedule)
    c = chain(compute_sections.si().set(queue="beat"),
              schedule_next_compute_sections.si().set(queue="beat"))
    c.apply_async(countdown=compute_sections_schedule*60)


@celery.task
def create_preview(photo_path, max_dim, low_res=True):
    logger.debug("Create Preview for %s in size %d, also in low resolution %s", photo_path, max_dim, low_res)
    path = get_full_path(photo_path)
    image = read_and_transpose(path)
    image.thumbnail((max_dim, max_dim), Image.ANTIALIAS)
    preview_path = get_preview_path(photo_path, str(max_dim), "high_res")
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path, optimize=True, progressive=True)

    if low_res:
        preview_path_low_res = get_preview_path(photo_path, str(max_dim), "low_res")
        os.makedirs(os.path.dirname(preview_path_low_res), exist_ok=True)
        image.thumbnail((max_dim/10, max_dim/10), Image.ANTIALIAS)
        image.save(preview_path_low_res, optimize=True, quality=20, progressive=False)

@celery.task(name="Recreate Previews")
def recreate_previews(dimension=400, low_res=True):
    logger.debug("Recreating Previews for size %d", dimension)
    for photo in Photo.query:
        create_preview.apply_async((photo.path, dimension, low_res), queue='process')

@celery.task(name="Split path and filename")
def split_filename_and_path():
    logger.debug("Splitting up filename and path for all photos again")
    for photo in Photo.query:
        photo.directory, photo.filename = os.path.split(photo.path)
    db.session.commit()