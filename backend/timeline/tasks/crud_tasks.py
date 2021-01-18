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

from timeline.domain import Photo, Exif, GPS, Status, Section, Person
import logging
from timeline.extensions import db, celery
import os
from PIL import Image, UnidentifiedImageError
from datetime import datetime
from pathlib import Path

from timeline.util.gps import get_labeled_exif, get_geotagging, get_coordinates, get_exif_value, get_lat_lon
from sqlalchemy import and_

from timeline.util.image_ops import read_and_transpose, resize_width
from timeline.util.path_util import get_rel_path, get_full_path, get_preview_path
from datetime import timedelta
from flask import current_app
from celery import chain


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


def set_status_dirty():
    status = Status.query.first()
    if not status.sections_dirty:
        status.sections_dirty = True


def create_photo(path, commit=True):
    logger.debug("Create new Photo %s", path)
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
    photo.exif = []
    photo.path = img_path
    photo.filename = os.path.basename(img_path)
    photo.width, photo.height = get_size(image)  # image.size
    exif_raw = image.getexif()
    exif_data = get_labeled_exif(exif_raw)
    geotags = get_geotagging(exif_raw)
    #latitude, longitude = get_coordinates(geotags)
    gps_data = get_lat_lon(geotags)
    if gps_data:
        # latitude, longitude = 
        gps = GPS()
        photo.gps = gps
        photo.gps.latitude, photo.gps.longitude = gps_data

    for key in exif_data.keys():
        raw_value = exif_data[key]
        try:
            value = get_exif_value(key, raw_value)
            if value is not None:
                exif = Exif()
                photo.exif.append(exif)

                exif.key, exif.value = key, str(value)

        except UnicodeDecodeError as u:
            logger.error("%s", img_path)

        # Now do extract important things such as date, gps infos and so on
        if key == 'DateTimeOriginal':
            try:
                # set photo date
                dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                photo.created = dt
                photo.no_creation_date = False
            except:
                logger.error("Error parsing Date for %s", img_path)

    if not photo.created:
        # there is either no exif date or it can't be parsed for the photo date, so we assumme it is old
        photo.created = datetime.today()
        photo.no_creation_date = True
        # they will be moved to the end later

    set_status_dirty()
    db.session.add(photo)

    if commit:
        db.session.commit()
    return photo.id

#def update_sections(photo):
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

    set_status_dirty()
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
    set_status_dirty()
    db.session.commit()

@celery.task(name="Sort old Photos to end")
def sort_old_photos():
    logger.debug("Sort undated Photos")
    status = Status.query.first()
    if not status.sections_dirty:
        logger.debug("sort_old_photos - nothing to do")
        return

    oldest_photo = Photo.query.order_by(Photo.created.asc()).first()
    if not oldest_photo:
        return
    min_date = oldest_photo.created - timedelta(days=1)
    photos = Photo.query.filter(Photo.no_creation_date == True)

    for photo in photos:
        #logger.debug("photo %i", photo.id)
        #logger.debug(min_date)
        photo.created = min_date - timedelta(seconds=1)

    db.session.commit()


@celery.task(name="Compute Sections and Sort Photos", ignore_result=True)
def compute_sections():
    logger.debug("Compute Sections")
    status = Status.query.first()

    if not status.sections_dirty and Photo.query.filter(Photo.section == None).count() == 0:
        logger.debug("compute_sections - nothing to do")
        return

    try:
        sort_old_photos()

        offset = 0
        batch_size = 300
        current_section = 0
        photos = Photo.query.order_by(Photo.created.desc()).limit(batch_size).all()
        last_batch_date = None
        section = None
        while len(photos) > 0:
            logger.debug("Sectioning next batch %i with %i initial photos", current_section, len(photos))
            photos_from_prev_batch = 0
            new_batch = True
            for photo in photos:
                if new_batch and last_batch_date != photo.created.date():
                    if section:
                        section.num_photos = len(section.photos)
                        logger.debug("Compute Sections - Closing Section with %i photos", section.num_photos)
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

            last_batch_date = photos[-1].created.date()
            photos = Photo.query.filter(Photo.created < photos[-1].created).order_by(Photo.created.desc()).limit(batch_size + add_limit).all()

    except Exception as exc:
        # this is bad, actually nothing should happen => refine this
        logger.error(exc)
        db.session.rollback()

    status.sections_dirty = False
    db.session.commit()
    logger.debug("Compute Sections - Done")

@celery.task(ignore_result=True)
def schedule_next_compute_sections(minutes=None):
    if minutes:
        compute_sections_schedule = minutes
    else:
        compute_sections_schedule = int(current_app.config['COMPUTE_SECTIONS_EVERY_MINUTES'])
    logger.debug("Scheduling next computing section in %i minutes", compute_sections_schedule)
    c = chain(compute_sections.s().set(queue="beat"), schedule_next_compute_sections.si().set(queue="beat"))
    c.apply_async(countdown=compute_sections_schedule*60)

@celery.task
def create_preview(photo_path, max_dim):
    # logger.debug("Create Preview for %s in size %d", photo_path, max_dim)
    path = get_full_path(photo_path)
    image = read_and_transpose(path)
    image.thumbnail((max_dim, max_dim), Image.ANTIALIAS)
    preview_path = get_preview_path(photo_path, str(max_dim))
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path)
