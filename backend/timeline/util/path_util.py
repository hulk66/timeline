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

import os

from flask import current_app




def get_rel_path(full_path):
    base_path = current_app.config['PHOTO_PATH']
    relpath = os.path.relpath(full_path, base_path)
    return relpath


def get_preview_path(rel_path, *prefix):
    return os.path.join(current_app.config['PREVIEW_PATH'], *prefix, rel_path)

def get_full_path(rel_path, *prefix):
    return os.path.join(current_app.config['PHOTO_PATH'], *prefix, rel_path)
