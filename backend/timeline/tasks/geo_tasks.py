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
from timeline.domain import Asset
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


@celery.task(name="Check GPS")
def check_gps(asset_id):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.warning("Can't check GPS data, asset may have been removed?")
        return

    if asset.gps_id:
        logger.debug("asset contains GPS data, scheduling reverse lookup: %s", asset.path)
        resolve_address.apply_async((asset_id,), queue='geo')
    else:
        logger.debug("asset contains no GPS data, nothing to do: %s", asset.path)


@celery.task(rate_limit="1/s", autoretry_for=(GeocoderTimedOut,GeocoderServiceError), name="Address Detection", ignore_result=True)
def resolve_address(asset_id):
    asset = Asset.query.get(asset_id)
    if not asset:
        logger.warning("Can not geo locate, asset may have been removed?")
        return

    logger.debug("Resolving GPS address for %s", asset.path)
    location = geolocator.reverse((asset.gps.latitude, asset.gps.longitude), timeout=10)
    asset.gps.display_address = location.address
    for part in ('city', 'country', 'country_code', 'road', 'state', 'postcode', 'county', 'village', 'municipality'):
        check_and_set(asset.gps, part, location.raw['address'])
    db.session.commit()
    logger.debug("Address resolved for %s", asset.path)
