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
import ssl

import certifi
import geopy.geocoders
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timeline.domain import Photo
from timeline.extensions import celery, db

logger = logging.getLogger(__name__)

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx
geopy.geocoders.options.default_timeout = 10
geolocator = geopy.Nominatim(scheme='http', user_agent='timeline')


def check_and_set(dest, name, src):
    if name in src:
        v = src[name]
        setattr(dest, name, v)


@celery.task(name="Checking for GPS Information", ignore_result=True)
def set_display_address(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        logger.warning("Can't check GPS data, photo may have been removed?")
        return

    if photo.gps_id:
        logger.debug("Photo contains GPS data, scheduling reverse lookup: %s", photo.path)
        resolve_address.apply_async((photo_id,), queue='process')
    else:
        logger.debug("Photo contains no GPS data, nothing to do: %s", photo.path)


@celery.task(rate_limit="1/s", autoretry_for=(GeocoderTimedOut,GeocoderServiceError), name="Address Detection", ignore_result=True)
def resolve_address(photo_id):
    photo = Photo.query.get(photo_id)
    if not photo:
        logger.warning("Can not geo locate, photo may have been removed?")
        return

    logger.debug("Resolving GPS address for %s", photo.path)
    location = geolocator.reverse((photo.gps.latitude, photo.gps.longitude), timeout=10)
    photo.gps.display_address = location.address
    for part in ('city', 'country', 'country_code', 'road', 'state', 'postcode', 'county', 'village', 'municipality'):
        check_and_set(photo.gps, part, location.raw['address'])
    db.session.commit()
    logger.debug("Address resolved for %s", photo.path)
