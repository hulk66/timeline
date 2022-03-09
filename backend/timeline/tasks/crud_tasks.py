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
import os.path
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO

from celery import chain
from flask import current_app
from PIL import Image, UnidentifiedImageError

from timeline.domain import Album, GPS, Exif, Person, Asset, Section, Status, DateRange, AssetType, TranscodingStatus
from timeline.extensions import celery, db
from timeline.util.gps import (get_exif_value, get_geotagging, get_gps_data,
                               get_labeled_exif, get_lat_lon)
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import (get_full_path, get_preview_path,
                                     get_rel_path)
from sqlalchemy import and_
from celery import signature
from celery import chain
from pillow_heif import register_heif_opener
import exiftool
import ffmpeg
from celery.exceptions import SoftTimeLimitExceeded
from distutils.util import strtobool

logger = logging.getLogger(__name__)
register_heif_opener()

exiftool = exiftool.ExifTool()
exiftool.start()


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


def create_asset(path: str, commit=True):
    logger.debug("Reading asset %s", path)
    # path = path.lower()
    if not Path(path).exists():
        logger.warning("File does not exist: %s", path)
        return None

    img_path = get_rel_path(path)

    asset = Asset.query.filter(Asset.path == img_path).first()
    if asset:
        logger.info("asset already exists %s. Skipping", img_path)
        return None

    if not os.path.exists(path):
        logger.error("File not found: %s")
        return None

    asset = Asset()
    asset.added = datetime.today()
    asset.ignore = False
    asset.exif = []
    asset.path = img_path
    asset.directory, asset.filename = os.path.split(img_path)
    _, ext = os.path.splitext(asset.filename)
    ext = ext[1:].lower()
    if ext in ("jpg", "jpeg"):
        asset.asset_type = AssetType.jpg_photo
    elif ext == "heic":
        asset.asset_type = AssetType.heic_photo
    elif ext == "mov":
        asset.asset_type = AssetType.mov_video
    elif ext == "mp4":
        asset.asset_type = AssetType.mp4_video

    if asset.is_photo():
        try:
            image = Image.open(path)
        except UnidentifiedImageError:
            logger.error("Invalid Image Format for %s", path)
            return None
        except FileNotFoundError:
            logger.error("File not found: %s")
            return None

        # this does not seem to be correct, there has to be a more elegant way
        if asset.asset_type == AssetType.heic_photo:
            asset.width, asset.height = image.size
        else:
            # transpose if necessary
            asset.width, asset.height = get_size(image)  # image.size
        _extract_exif_data(asset, image)
    else:
        md = exiftool.get_metadata(path)
        asset.video_preview_generated = False
        asset.video_fullscreen_transcoding_status = TranscodingStatus.NONE
        asset.video_fullscreen_generated_progress = 0
        
        asset.width = md.get("QuickTime:ImageWidth")
        asset.height = md.get("QuickTime:ImageHeight")

        if md.get('Composite:Rotation') == 90 or md.get('Composite:Rotation') == 270:
            asset.width, asset.height = asset.height, asset.width

        lat = md.get("Composite:GPSLatitude")
        long = md.get("Composite:GPSLongitude")
        if lat and long:
            gps = GPS()
            asset.gps = gps
            asset.gps.latitude, asset.gps.longitude = lat, long

        dateStr = md.get("QuickTime:MediaCreateDate")
        if dateStr:
            dt = datetime.strptime(str(dateStr), "%Y:%m:%d %H:%M:%S")
            asset.created = dt
            asset.no_creation_date = False

    # asset.directory = os.path.
    db.session.add(asset)
    # sort_asset_into_date_range(asset, commit = False)
    add_to_last_import(asset)
    if commit:
        # perform already a commit, so that in case a parallel worker inserts something in
        # the section and we get a duplicate error, the photo is already there
        # and will be inserted in the next round
        db.session.commit()

    insert_asset_into_section(asset)

    if commit:
        db.session.commit()
    return asset.id


@celery.task(name="Extract Exif Data for all assets")
def extract_exif_all_assets(overwrite):
    logger.debug("Extract Exif and GPS for all assets")
    for asset in Asset.query:
        c = chain(
            signature("Extract Exif", args=(
                asset.id, overwrite), queue='process'),
            signature("Check GPS", args=(asset.id,),
                      queue="analyze", immutable=True)
        )
        c.apply_async()


@celery.task(name="Extract Exif")
def extract_exif_data(asset_id, overwrite):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.warning("asset with ID %d does not exist", asset_id)
        return
    if overwrite or not asset.exif:
        _extract_exif_data(asset)
    db.session.commit()


def _extract_exif_data(asset, image=None):

    logger.debug("Extract Exif Data for asset %s", asset.path)
    if not image:
        path = get_full_path(asset.path)

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
        asset.gps = gps
        asset.gps.latitude, asset.gps.longitude = gps_data

    asset.exif = []
    for key in exif_data.keys():
        raw_value = exif_data[key]
        try:
            value = get_exif_value(key, raw_value)
            if value is not None:
                exif = Exif()
                asset.exif.append(exif)

                exif.key, exif.value = key, str(value)

        except UnicodeDecodeError:
            logger.error("%s", img_path)

        # User either DateTimeOriginal or not available any other DateTime
        # or (key.startswith("DateTime") and asset.created is None):
        if key == 'DateTimeOriginal':
            try:
                # set asset date
                dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                asset.created = dt
                asset.no_creation_date = False
            except ValueError:
                logger.error("%s can not be parsed as Date for %s",
                             str(value), asset.path)

    if not asset.created:
        # there is either no exif date or it can't be parsed for the asset date, so we assumme it is old
        asset.created = datetime.today()
        asset.no_creation_date = True
        # they will be moved to the end later


def insert_asset_into_section(asset):

    if Status.query.first().in_sectioning:
        # will be done later otherwise we have to mess around with transactions blocking each other
        return

    section = Section.query.filter(asset.created >= Section.oldest_date).order_by(
        Section.oldest_date.asc()).first()
    if not section:
        # try to look from the other direction: find the section where the date of the current asset is older than the ol
        section = Section.query.filter(asset.created < Section.newest_date).order_by(
            Section.newest_date.desc()).first()
        if not section:
            section = Section()
            section.newest_date = datetime.today()
            section.oldest_date = asset.created
            db.session.add(section)
        else:
            if asset.created < section.oldest_date:
                section.oldest_date = asset.created
    else:
        # we have found a section where the photo is more recent than the oldest asset of the section
        # now check if the asset is also more recent than the newest phot
        if asset.created > section.newest_date:
            section.newest_date = asset.created

    section.assets.append(asset)


def add_to_last_import(asset):
    status = Status.query.first()
    status.sections_dirty = True
    album = Album.query.get(status.last_import_album_id)

    if album is None:
        album = Album()
        album.name = "Last Import"
        db.session.add(album)
        status.last_import_album_id = album.id

    if status.next_import_is_new:
        album.assets = []
        status.next_import_is_new = False

    album.assets.append(asset)

# def update_sections(asset):
#
#    sec = Sec.query.find( and_(Sec.start_date <= asset.created, asset.created < Sec.end_date)).first()
#    if sec:
#        if size(sec) > MAX_SEC_SIZE:
#
#        else:
#            # all good, nothing to do


def delete_asset(asset: Asset):
    status = Status.query.first()
    db.session.delete(asset)
    # remove empty albums
    albums = Album.query.filter(Album.assets == None)
    for album in albums:
        if album.id != status.last_import_album_id:
            # do not remove the Last Import Album
            db.session.delete(album)
    # same for persons
    for person in Person.query.filter(Person.faces == None):
        db.session.delete(person)


def _delete_asset_by_path(path):
    for p in Asset.query.filter(Asset.path == path):
        _delete_asset(p)


@celery.task(mame="Delete asset")
def delete_asset_by_path(img_path, commit=True):
    logger.debug("Delete asset %s", img_path)
    path = get_rel_path(img_path)
    _delete_asset_by_path(path)

    Status.query.first().sections_dirty = True
    if commit:
        db.session.commit()


@celery.task(mame="Modify asset")
def modify_asset(img_path):
    logger.debug("Modify asset %s", img_path)

    delete_asset(img_path, commit=False)
    create_asset(img_path, commit=False)
    db.session.commit()


@celery.task(name="Move asset")
def move_asset(img_path_src, img_path_dest):
    logger.debug("Move asset from %s to %s", img_path_src, img_path_dest)
    path = get_rel_path(img_path_src)
    assets = Asset.query.filter(Asset.path == path).all()

    if len(assets) > 0:
        assets[0].path = get_rel_path(img_path_dest)
    Status.query.first().sections_dirty = True
    db.session.commit()


def sort_asset_into_date_range_task(asset_id):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.error(
            "Something is wrong. asset with id %d not found. Deleted already?")
        return
    sort_asset_into_date_range(asset, commit=True)


def find_date_range(asset: Asset) -> DateRange:
    date_range = DateRange.query.filter(asset.created >= DateRange.start_date).order_by(
        DateRange.start_date.desc()).with_for_update().first()
    if not date_range:
        date_range = DateRange()
        date_range.start_date = asset.created.date()
        db.session.add(date_range)
        db.session.commit()
    return date_range


def find_date_range2(asset: Asset) -> DateRange:
    date_range = DateRange.query.filter(and_(
        DateRange.end_date > asset.created, asset.created >= DateRange.start_date)).first()

    if not date_range:
        # no specific date range was found
        # so try to find one bloew or up

        date_range = DateRange.query.filter(
            DateRange.end_date > asset.created).order_by(DateRange.end_date.asc()).first()

        if not date_range:
            date_range = DateRange.query.filter(asset.created >= DateRange.start_date).order_by(
                DateRange.start_date.desc()).first()

            if not date_range:
                date_range = DateRange()
                date_range.start_date = asset.created
                date_range.end_date = date_range.start_date + timedelta(days=1)
                db.session.add(date_range)

    if asset.created >= date_range.end_date:
        date_range.end_date = asset.created
    if asset.created < date_range.start_date:
        date_range.start_date = asset.created
    return date_range


def find_upper_start_date(date_range: DateRange) -> DateRange:
    upper_date_range = DateRange.query.filter(
        DateRange.start_date > date_range.start_date).order_by(DateRange.start_date.desc()).first()
    if not upper_date_range:
        upper_date_range = DateRange()
        #  = date_range.start_date.date() +  timedelta(days = 1)
        upper_date_range.start_date = date_to_datetime(datetime.today().date())
        db.session.add(upper_date_range)
    return upper_date_range


def date_to_datetime(d: datetime.date):
    return datetime(year=d.year, month=d.month, day=d.day)


def split_date_range(date_range: DateRange):
    upper_date_range = find_upper_start_date(date_range)
    if upper_date_range:

        delta = upper_date_range.start_date - date_range.start_date
        if delta.days > 1:
            # Only split it if the data range is more than just one day
            # if we exceeed the number of assets in one day then we just accept it
            new_date_range = DateRange()
            new_date_range.start_date = upper_date_range.start_date - \
                timedelta(days=int(delta.days / 2))
            db.session.add(new_date_range)


def level_date_ranges(start_asset: Asset = None):
    logger.debug("Level data ranges for sectioning")

    status = Status.query.first()

    if not status.sections_dirty and Asset.query.filter(asset.section == None).count() == 0:
        logger.debug("Level Date Ranges- nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return

    if not start_asset:
        start_asset = Asset.query.order_by(Asset.created.asc()).first()

    lower_date_range = DateRange.query.filter(
        start_asset.created >= DateRange.start_date).order_by(DateRange.start_date.desc()).first()
    if not lower_date_range:
        lower_date_range = DateRange()
        lower_date_range.start_date = date_to_datetime(
            start_asset.created.date())
        db.session.add(lower_date_range)

    upper_date_range = find_upper_start_date(lower_date_range)
    assets = Asset.query.filter(and_(upper_date_range.start_date >
                                Asset.created, Asset.created >= lower_date_range.start_date))

    if assets.count() < 300:
        # continue here
        pass
    if DateRange.query.count() == 0:
        # create initial DateRange
        date_range = DateRange()


def sort_asset_into_date_range(asset, commit=True):
    logger.debug("Insert asset into Section Range for %s", asset.path)

    date_range = find_date_range(asset)
    assets_in_range = Asset.query.filter(
        asset.created >= date_range.start_date)

    if assets_in_range.count() > 300:
        split_date_range(date_range)
    elif assets_in_range.count() == 0:
        db.session.remove(date_range)
    else:
        if asset.created < date_range.start_date:
            date_range.start_date = asset.created
    if commit:
        db.session.commit()


@celery.task(name="Sort old assets to end")
def sort_old_assets():
    logger.debug("Sort undated assets")
    status = Status.query.first()
    if not status.sections_dirty:
        logger.debug("sort_old_assets - nothing to do")
        return

    oldest_asset = Asset.query.filter(
        Asset.ignore == False).order_by(Asset.created.asc()).first()
    if not oldest_asset:
        return
    min_date = oldest_asset.created - timedelta(days=1)
    assets = Asset.query.filter(Asset.no_creation_date == True)

    for asset in assets:
        # logger.debug("asset %i", asset.id)
        # logger.debug(min_date)
        asset.created = min_date
        min_date -= timedelta(seconds=1)

    db.session.commit()


def new_import():
    album = Album.query.get(0)
    if album is None:
        album = Album()
        album.id = 0
        album.name = 'Last Import'
    album.assets = []


@celery.task(ignore_result=True, soft_time_limit=900)
def compute_sections():
    logger.debug("Sectioning assets")

    status = Status.query.first()

    if not status.sections_dirty and Asset.query.filter(Asset.section == None).count() == 0:
        logger.debug("Sectioning assets - nothing to do")
        status.next_import_is_new = True
        db.session.commit()

        # if there is nothing new it is a good point to start the event finder
        celery.send_task("Find Events", queue="analyze")        
        return
    sort_old_assets()

    status.in_sectioning = True
    db.session.commit()

    batch_size = 200
    current_section = 1
    # Get all assets sorted descending, meaning the newest first
    assets = Asset.query.filter(Asset.ignore == False).order_by(
        Asset.created.desc()).limit(batch_size).all()
    while len(assets) > 0:
        section = Section.query.get(current_section)
        if not section:
            logger.debug("Creating new Section")
            section = Section()
            section.id = current_section
            db.session.add(section)

        oldest_asset = assets[-1]

        for asset in assets:
            asset.section = section

        # check if there are other asset which have by accident the same creation date
        same_date_assets = Asset.query.filter(and_(Asset.created == oldest_asset.created, Asset.id != oldest_asset.id))
        for a in same_date_assets:
            a.section = section

        logger.debug("Initial Sectioning %d", current_section)    
        current_section += 1
        assets = Asset.query \
            .filter(and_(Asset.ignore == False, Asset.created < oldest_asset.created)) \
            .order_by(Asset.created.desc()).limit(batch_size).all()

    # now we have section with batch_size photos in it. Next we have to make sure
    # a section ends always with all photos of the last day in it
    logger.debug("Finetuning sections")
    sections = Section.query.order_by(Section.id.asc())
    last_day_of_prev_section = None
    previous_section = None
    for section in sections:
        logger.debug("Finetuning section %d", section.id)

        # get all assets from current section that are taken on the same day as the last one of the previous section
        if last_day_of_prev_section:
            next_day = last_day_of_prev_section + timedelta(days=1)
            same_day_assets = Asset.query.filter(and_(Asset.section == section, Asset.ignore == False, Asset.created >= last_day_of_prev_section, Asset.created < next_day)).all()
            if len(same_day_assets) > 0:
                logger.debug("Moving %d assets from section %d to section %d", len(same_day_assets), section.id, previous_section.id)
                for asset in same_day_assets:
                    asset.section = previous_section
        previous_section = section
        # get the oldest/last asset of the current section
        last_asset_of_this_section = Asset.query.filter(Asset.section == section).order_by(Asset.created.asc()).first()
        if last_asset_of_this_section:
            last_day_of_prev_section = date_to_datetime(last_asset_of_this_section.created)

    # Finally remove all empty sections and tidy up the numbering
    current_section = 1
    sections = Section.query.order_by(Section.id.asc()).all()
    for section in sections:
        # print(Asset.query.filter(Asset.section == section).order_by(Asset.created.desc()))
        assets = Asset.query.filter(Asset.section == section).order_by(Asset.created.desc()).all()
        if len(assets) > 0:
            if current_section != section.id:
                new_section = Section()
                new_section.id = current_section
                db.session.add(new_section)
                for asset in assets:
                    asset.section = new_section
                db.session.delete(section)            
            current_section += 1
            # get oldest and newest date
            section.newest_date = assets[0].created
            section.oldest_date = assets[-1].created
            
        else:
            logger.debug("no assets in section %i, removing it", section.id)
            db.session.delete(section)

    status.in_sectioning = False
    status.sections_dirty = False
    db.session.commit()
    logger.debug("Sectioning done - ok")




@celery.task(ignore_result=True, soft_time_limit=900)
def compute_sections_old2():
    logger.debug("Sectioning assets")

    status = Status.query.first()

    if not status.sections_dirty and Asset.query.filter(Asset.section == None).count() == 0:
        logger.debug("Sectioning assets - nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return
    sort_old_assets()

    status.in_sectioning = True
    db.session.commit()

    try: 
        batch_size = 200
        current_section = 1

        # Get all assets sorted descending, meaning the newest first
        assets = Asset.query.filter(Asset.ignore == False).order_by(
            Asset.created.desc()).limit(batch_size).all()
        while len(assets) > 0:
            # get the date of the oldest asset of that batch
            oldest_asset = assets[-1]
            # Find all assets that are on the same day as the oldest asset
            oldest_asset_prev_day = date_to_datetime(
                oldest_asset.created.date() - timedelta(days=1))
            # now find all assets that are older as the oldest asset from batch but newer as the next day
            same_day_assets = Asset.query.filter(and_(
                Asset.ignore == False, Asset.created < oldest_asset.created, Asset.created > oldest_asset_prev_day)).all()

            # these assets will be added to the same section, so that each setion always start with a new day
            logger.debug("Sectioning %i assets", len(
                assets) + len(same_day_assets))
            section = Section.query.get(current_section)
            if not section:
                logger.debug("Creating new Section")
                section = Section()
                db.session.add(section)
                # section.id = current_section

            #Asset.query.filter( and_(asset.ignore == False, asset.created > oldest_asset.created, asset.created < oldest_asset_prev_day)).update( {asset.section: section}, synchronize_session=False)

            for asset in assets:
                asset.section = section
            for asset in same_day_assets:
                asset.section = section
            section.newest_date = assets[0].created
            if len(same_day_assets) > 0:
                section.oldest_date = same_day_assets[-1].created
            else:
                section.oldest_date = oldest_asset.created
            assets = Asset.query \
                .filter(and_(Asset.ignore == False, Asset.created <= oldest_asset_prev_day)) \
                .order_by(Asset.created.desc()).limit(batch_size).all()
            current_section += 1

        # Section.query.filter(Section.id >= current_section).delete()
        status.in_sectioning = False
        status.sections_dirty = False
        logger.debug("Sectioning done - ok")
    except SoftTimeLimitExceeded:
        logger.error("Compute Sections did not come to an end within 900sec, cleaning up for now")
        status.in_sectioning = False
        status.sections_dirty = True
        logger.debug("Sectioning done - not ok")
    db.session.commit()



def compute_sections_old():
    logger.debug("Compute Sections")
    status = Status.query.first()

    if not status.sections_dirty and Asset.query.filter(Asset.section == None).count() == 0:
        logger.debug("compute_sections - nothing to do")
        status.next_import_is_new = True
        db.session.commit()
        return

    sort_old_assets()

    offset = 0
    batch_size = 200
    current_section = 0
    assets = Asset.query.filter(Asset.ignore == False).order_by(
        Asset.created.desc()).limit(batch_size).all()
    prev_batch_date = None
    last_batch_date = None
    section = None
    initial = True

    while len(assets) > 0:
        logger.debug("Sectioning next batch %i with %i initial assets",
                     current_section, len(assets))
        assets_from_prev_batch = 0
        add_limit = 0
        new_batch = True
        for asset in assets:
            if initial or (new_batch and last_batch_date and last_batch_date.date() != Asset.created.date()):
                initial = False
                if section:
                    section.num_assets = len(section.assets)
                    logger.debug(
                        "Compute Sections - Closing Section with %i assets", section.num_assets)
                    section.start_date = None
                add_limit = assets_from_prev_batch
                section = Section.query.get(current_section)
                if not section:
                    logger.debug("Creating new Section")
                    section = Section()
                    db.session.add(section)
                    section.id = current_section

                current_section += 1
                new_batch = False
            else:
                assets_from_prev_batch += 1
            offset += 1
            asset.section = section

        last_batch_date = assets[-1].created
        if prev_batch_date == last_batch_date:
            # make sure to always have a date break in the set of assets
            # otherwise we might come into an endless loop
            # let's see if this solves this strange problem
            last_batch_date -= timedelta(seconds=1)
        prev_batch_date = last_batch_date
        assets = Asset.query \
            .filter(Asset.created < last_batch_date) \
            .order_by(Asset.created.desc()).limit(batch_size + add_limit).all()

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


def create_jpg_preview(asset: Asset, max_dim: int, low_res=True):
    full_path = get_full_path(asset.path)
    if asset.asset_type == AssetType.jpg_photo:
        # not clear but it seems to be only necessary for jpg
        image = read_and_transpose(full_path)
    else:
        # solves orientation in thumbnails
        image = Image.open(full_path)
        #out = io.BytesIO()
        #image.save(out, format="JPEG")
        #image = Image.open(out)

    ar = image.width / image.height
    width = max_dim * ar
    image.thumbnail((width, max_dim), Image.ANTIALIAS)
    preview_path = get_preview_path(
        asset.path, ".jpg", str(max_dim), "high_res")
    # print(preview_path)
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    image.save(preview_path, optimize=True, progressive=True)

    if low_res:
        preview_path_low_res = get_preview_path(
            asset.path, ".jpg", str(max_dim), "low_res")
        os.makedirs(os.path.dirname(preview_path_low_res), exist_ok=True)
        image.thumbnail((width/10, max_dim/10), Image.ANTIALIAS)
        image.save(preview_path_low_res, optimize=True,
                   quality=20, progressive=False)




#@celery.task
#def create_photo_preview(asset: Asset):
#    logger.debug("Create Photo Preview for %s", asset.path)
#    _create_jpg_preview(asset, 2160, False)
#    _create_jpg_preview(asset, 400, True)


#@celery.task
#def create_video_preview(asset: Asset):
#    logger.debug("Create Video Preview for %s", asset.path)
#    _create_video_preview(asset, 400)


@celery.task
def create_preview(asset_id: int):
    asset = Asset.query.get(asset_id)
    if asset.is_photo():
        create_jpg_preview(asset, 2160, False)
        create_jpg_preview(asset, 400, True)
    elif asset.is_video():
        celery.send_task("Create Preview Video", (asset_id, 400), queue="transcode")
        video_create_on_demand = bool(strtobool(current_app.config['VIDEO_TRANSCODE_ON_DEMAND']))
        if not video_create_on_demand:
            celery.send_task("Create Fullscreen Video", (asset_id,), queue="transcode")

        # create_preview_video.apply_async( (asset_id, 400), queue="transcode")
        # create_fullscreen_video.apply_async( (asset_id,), queue="transcode")
    else:
        logger.error(
            "create_preview: Something went wrong. Should be a photo or a video")


@celery.task(name="Recreate Previews")
def recreate_previews(dimension=400, low_res=True):
    logger.debug("Recreating Previews for size %d", dimension)
    for asset in Asset.query:
        create_preview.apply_async(
            (asset.path, dimension, low_res), queue='process')


@celery.task(name="Split path and filename")
def split_filename_and_path():
    logger.debug("Splitting up filename and path for all assets again")
    for asset in Asset.query:
        asset.directory, asset.filename = os.path.split(asset.path)
    db.session.commit()


@celery.task()
def _resync_asset(asset_id):
    # logger.debug("Resync asset")
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.error(
            "Something is wrong. asset with id %d not found. Deleted already?", asset_id)
        return
    path = get_full_path(asset.path)
    if not os.path.exists(path):
        # We are out of sync. The database references a asset which does not exist in the filesystem anymore
        logger.debug(
            "asset %s no longer exists. Remove it from the catalog", asset.path)
        _delete_asset(asset)
    db.session.commit()


@celery.task(name="Resync assets")
def resync_assets():
    logger.debug(
        "Sync assets. Ensure the Database is reflecting the filesystem")
    for asset in Asset.query:
        _resync_asset.apply_async((asset.id,), queue="process")
