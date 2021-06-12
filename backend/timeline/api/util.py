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

import flask


def list_as_json(list, excludes=None):
    result = [element.to_dict(rules=excludes) for element in list]
    return flask.jsonify(result)


def list_as_json_only(list, only):
    result = [element.to_dict(only=only) for element in list]
    return flask.jsonify(result)
