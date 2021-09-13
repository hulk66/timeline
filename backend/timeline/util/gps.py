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
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS

logger = logging.getLogger(__name__)

exif_tags_exclude_list = ['ComponentsConfiguration', 'JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'MakerNote', 'ShutterSpeedValue', 'ApertureValue']
# based on https://gist.github.com/erans/983821

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format

    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)


def get_exif_location_old(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """
    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degress(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degress(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon

    return lat, lon


def get_exif_location(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """
    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degress(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degress(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon

    return lat, lon


def get_decimal_from_dms(dms, ref):
    degrees = dms[0][0] / dms[0][1]
    minutes = dms[1][0] / dms[1][1] / 60.0
    seconds = dms[2][0] / dms[2][1] / 3600.0

    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(degrees + minutes + seconds, 5)


def get_coordinates(geotags):
    lat, lon = None, None
    try:
        if geotags:
            lat = get_decimal_from_dms(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])
            lon = get_decimal_from_dms(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])
    except KeyError:
        pass

    return (lat, lon)


get_float = lambda x: float(x[0]) / float(x[1])


def convert_to_degrees(value):
    return value[0] + (value[1] / 60.0) + (value[2] / 3600.0)


def get_lat_lon(geotags):
    try:
        gps_latitude = geotags['GPSLatitude']
        gps_latitude_ref = geotags['GPSLatitudeRef']
        gps_longitude = geotags['GPSLongitude']
        gps_longitude_ref = geotags['GPSLongitudeRef']

        lat = convert_to_degrees(gps_latitude)
        if gps_latitude_ref != "N":
            lat *= -1

        lon = convert_to_degrees(gps_longitude)
        if gps_longitude_ref != "E":
            lon *= -1
        return lat, lon
    except KeyError:
        return None


def get_labeled_exif(exif):
    labeled = {}
    if exif:
        for (key, val) in exif.get_ifd(0x8769).items():
            label = TAGS.get(key)
            if val and label and label not in exif_tags_exclude_list:
                if isinstance(val, bytes):
                    val = val.decode("utf-8", "replace")

                labeled[label] = val

    return labeled


def get_exif_table(exif_data) -> dict:
    exif_table = {}
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        exif_table[decoded] = value

def get_gps_data(exif_table: dict) -> dict:
    gps_info = {}
    for key in exif_table['GPSInfo'].keys():
        decode = GPSTAGS.get(key,key)
        gps_info[decode] = exif_table['GPSInfo'][key]

    return gps_info

def get_exif_value(key, raw_value):
    v = str(raw_value)[0:100]
    if key in ("XResolution", "YResolution"):
        n = float(raw_value.numerator)
        d = float(raw_value.denominator)
        v = round(n/d)

    if key == "ExposureTime":
        n = float(raw_value.numerator)
        d = float(raw_value.denominator)
        sec = round(d/n)

        v = "1/" + str(sec)
    elif key in ("FNumber", "FocalLength", "ExposureBiasValue"):
        v = round(float(raw_value.numerator) / float(raw_value.denominator))
    return v


def get_geotagging(exif) -> dict:
    geotagging = {}
    if exif:
        dictionary = exif.get_ifd(0x8825)
        for (key, val) in GPSTAGS.items():
            if key in dictionary:
                geotagging[val] = dictionary[key]

    return geotagging
