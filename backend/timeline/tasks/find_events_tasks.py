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
from tokenize import String
import numpy
from celery import chain
from flask import current_app
from pymysql.err import InternalError
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN
from sqlalchemy import and_, or_
from timeline.domain import Asset, Event, GPS, Album, AlbumType, Status
from timeline.extensions import celery, db
from datetime import datetime
logger = logging.getLogger(__name__)


def find_name(asset_id_list:numpy.ndarray, min_date:datetime) -> String:
    gps = GPS.query.join(Asset).filter( Asset.id.in_(asset_id_list) )
    location = None
    result =  min_date.strftime("%B %Y")
    if gps:
        location = gps.first()
    if location:
        result += " - "
        if location.village:
            result += location.village
        elif location.city:
            result += location.city
        elif location.municipality:
            result += location.municipality
        elif location.county:
            result += location.county
        if location.country:
            result += ", " + location.country 

    return result      

@celery.task(name="Find Events")
def find_events():
    status = Status.query.first()
    if not status.find_events_needed:
        logger.debug("Find Events: Nothing to do")
        return

    logger.debug("Find Events: Go")
    all_assets = Asset.query.with_entities(Asset.id, Asset.created).all()
    ids, creation_dates = zip(*all_assets)
    ids = numpy.asarray(ids)
    timestamps = map(lambda d: d.timestamp(), creation_dates)
    timestamps = numpy.asarray(tuple(timestamps))

    asset_sample = int(current_app.config['EVENT_MIN_SAMPLES'])
    epsilon = int(current_app.config['EVENT_HOURS_EPSILON']) * 3600
    dbscan = DBSCAN(eps=epsilon, min_samples=asset_sample).fit(timestamps.reshape(-1,1))
    labels = dbscan.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

    for cluster in range(n_clusters - 1):
        indices = numpy.where(labels == cluster)
        cluster_elements = timestamps[indices]
        asset_id_list = ids[indices]
        start = datetime.fromtimestamp(cluster_elements.min())
        end = datetime.fromtimestamp(cluster_elements.max())
        event = Event.query.filter( and_(Event.start_date == start, Event.end_date == end )).first()
        if event:
            logger.debug("Found Event: has already been identified")
            # do nothing, the found window is within an already existing event
            pass
        else: 
            event = Event.query.filter( and_(Event.start_date == start, Event.end_date <= end )).first()
            if event:
                logger.debug("Found Event: extending end date")
                event.end_date = end
            else:
                event = Event.query.filter( and_(Event.start_date >= start, Event.end_date == end )).first()
                if event:
                    logger.debug("Found Event: extending start date")
                    event.start_date = start
                else:
                    logger.debug("New Event: From " + start.isoformat()  +  "To " + end.isoformat())
                    event = Event()
                    event.start_date = start
                    event.end_date = end
                    event.name = find_name(asset_id_list, start)
                    event.ignore = False
                    db.session.add(event)

                    album = Album()
                    album.type = AlbumType.EVENT
                    album.start_date = start
                    album.end_date = end
                    album.name = event.name
                    db.session.add(album)

    status.find_events_needed = False
    db.session.commit()






