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

import csv
import json
import logging

from timeline.domain import Thing
from timeline.extensions import db

LABEL_NAME = 'LabelName'
SUBCATEGORY = 'Subcategory'
log = logging.getLogger(__name__)


def insert_things(csv_thing_file):
    log.info("insert things from CSV")
    f = open(csv_thing_file)
    csv_reader = csv.reader(f)
    i = 0
    first_run = True
    init_required = True
    for row in csv_reader:
        if i % 100 == 0:
            log.debug("Thing No. %i", i)
        i += 1
        id = row[0]
        label = row[1]

        if first_run:
            t = Thing.query.get(id)
            first_run = False
            if t:
                init_required = False
                break

        t = Thing(id = id, label_en = label)
        db.session.add(t)
    db.session.commit()
    return init_required

def set_hierarchy(hierarchy_file):
    log.info("set hierarchy between things")

    f = open(hierarchy_file)
    data = json.load(f)
    top_level_elements = data[SUBCATEGORY]
    for e in top_level_elements:
        h(e, None)

    db.session.commit()

def h(element, parent):

    if parent:

        element_id = element[LABEL_NAME]
        parent_id = parent[LABEL_NAME]
        parent_thing = Thing.query.get(parent_id)
        thing = Thing.query.get(element_id)
        if thing and parent_thing:
            log.debug("Make %s parent of %s", parent_thing.label_en, thing.label_en)
            thing.parent_id = parent_thing.id
        else:
            if not thing:
                log.error("Thing not found for %s", element_id)
            if not parent_thing:
                log.error("Parent not found for %s", parent_id)

    if SUBCATEGORY in element:
        sub_categories = element[SUBCATEGORY]
        for cat in sub_categories:
            h(cat, element)
