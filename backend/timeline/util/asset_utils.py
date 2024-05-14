'''
Copyright (C) 2021, 2022, 2023, 2024 Tobias Himstedt, Sergii Puliaiev


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
from datetime import datetime

from PIL import Image, UnidentifiedImageError
from timeline.api.util import parse_exif_date

from timeline.domain import GPS, Exif, Asset, AssetType, TranscodingStatus
from timeline.util.asset_creation_result import AssetCreationResult
from timeline.util.gps import (get_exif_value, get_geotagging, get_gps_data,
                               get_labeled_exif, get_lat_lon)
from timeline.util.image_ops import read_and_transpose
from timeline.util.path_util import (get_full_path, get_preview_path,
                                     get_rel_path)
from simple_file_checksum import get_checksum
from sqlalchemy import and_
from pillow_heif import register_heif_opener
import exiftool

logger = logging.getLogger(__name__)

register_heif_opener()

exiftool = exiftool.ExifTool()
exiftool.start()

CURRENT_VERSION = 2

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


def populate_asset(asset: Asset, result: AssetCreationResult):
    if not asset:
        asset = Asset()
        asset.added = datetime.today()
        asset.ignore = False
        asset.exif = []
        asset.path = get_rel_path(result.path)
        asset.version = 0
        result.created_in_db = True

    if asset.version < 1:
        result.versions_applied.append(1)
        populate_asset_v1(asset, result)
    
    if asset.version < 2:
        result.versions_applied.append(2)
        populate_asset_v2(asset, result)
    
    # upgrading asset to the current version
    asset.version = CURRENT_VERSION
    result.version_saved = asset.version
    
    return asset
    
    
def identify_type(asset: Asset):
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

    
def populate_asset_v1(asset: Asset, result: AssetCreationResult):
    asset.directory, asset.filename = os.path.split(asset.path)
    identify_type(asset)

    if asset.is_photo():
        _extract_image_exif_data(asset, result)
    else:
        _extract_video_exif_data(asset, result)


def populate_asset_v2(asset: Asset, result: AssetCreationResult):
    path = get_full_path(asset.path)
    stats = os.stat(path)
    asset.file_size = stats.st_size
    asset.checksum = get_checksum(path, algorithm="MD5")
    asset.checksum_type = 'MD5'


def _extract_video_exif_data(asset, result: AssetCreationResult):
    logger.debug("Extract Video Exif Data for asset %s", asset.path)
    path = get_full_path(asset.path)
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

    date_str = md.get("QuickTime:MediaCreateDate")
    if date_str:
        try:
            dt = parse_exif_date(date_str)
            asset.created = dt
            asset.no_creation_date = False
        except ValueError:
            logger.info("Could not parse Date for Video")
            asset.created = datetime.today()
            asset.no_creation_date = True

def _get_exif_date(exif_data, key: str, path: str):
    raw_value = exif_data.get(key)
    if not raw_value:
        return None
    try:
        value = get_exif_value(key, raw_value)
    except UnicodeDecodeError:
        logger.error("Unicode decode error for key %s for path %s", key, path)
        return None

    try:
        # set asset date
        return parse_exif_date(value)
    except ValueError:
        logger.error("%s = %s can not be parsed as Date for %s", key, 
                    str(value), path)

    
def _extract_image_exif_data(asset: Asset, result: AssetCreationResult):
    logger.debug("Extract Image Exif Data for asset %s", asset.path)
    path = get_full_path(asset.path)

    try:
        image = Image.open(path)
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
                logger.error("%s", asset.path)

        asset.created = _get_exif_date(exif_data, "DateTimeOriginal", asset.path) or \
                        _get_exif_date(exif_data, "DateTime", asset.path) or \
                        _get_exif_date(exif_data, "DateTimeDigitized", asset.path)
        image.close()
    except UnidentifiedImageError:
        logger.error("Invalid Image Format for %s", path)
        result.invalid = True
        return None
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        result.file_present = False
        return None
    finally:
        if not asset.created:
            # there is either no exif date or it can't be parsed for the asset date, so we assumme it is old
            asset.created = datetime.today()
            asset.no_creation_date = True
            # they will be moved to the end later
        else:
            asset.no_creation_date = False

def dedup_header(id: str, queue_name: str):
    # RabbitMQ Deduplication plugin
    # https://github.com/noxdafox/rabbitmq-message-deduplication/tree/main
    
    return {
        "x-deduplication-header": f"{queue_name}:{id}"
    }
    