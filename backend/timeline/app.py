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
from timeline.extensions import db, celery
from timeline.api import views, photos, admin, inspect, albums
import logging
import pymysql
import numpy
from logging.handlers import RotatingFileHandler
from flask import Flask
import sqlalchemy


def create_app(testing=False, cli=False, env=None):
    """Application factory, used to create application"""
    app = Flask(__name__)
          
    app.config.from_object("timeline.config")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if env:
        app.config.from_pyfile(env)
    if testing is True:
        app.config["TESTING"] = True

    # app.config['SQLALCHEMY_ECHO'] = True
    configure_extensions(app, cli)
    # configure_apispec(app)
    register_blueprints(app)
    # init_celery(app)

    @app.route('/')
    def index():
        return flask.render_template("index.html")

    return app


def configure_extensions(app, cli):
    """configure flask extensions
    """

    pymysql.converters.encoders[numpy.float64] = pymysql.converters.escape_float
    pymysql.converters.conversions = pymysql.converters.encoders.copy()
    pymysql.converters.conversions.update(pymysql.converters.decoders)

    create_db(app)
    db.init_app(app)
    db.create_all(app=app)
    celery.init_app(app)


def register_blueprints(app):
    """register all blueprints for application
    """
    app.register_blueprint(views.blueprint)
    app.register_blueprint(photos.blueprint)
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(inspect.blueprint)
    app.register_blueprint(albums.blueprint)


def init_celery(app=None):
    app = app or create_app()
    # celery.conf.update(app.config.get("CELERY", {}))
    # celery.conf.update(result_backend=timeline.config.CELERY_RESULT_BACKEND, broker_url=timeline.config.CELERY_RESULT_BACKEND)
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def setup_logging(app, logfile_name):
    log_path = app.config["LOG_PATH"]
    logger = logging.getLogger("timeline")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)15s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(log_path + '/' + logfile_name, maxBytes=10**7, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_db(app):
    create = app.config["CREATE_DATABASE"]
    if create:
        db_host = app.config["DB_HOST"]
        db_pw = app.config["DB_SUPER_USER"]
        engine = sqlalchemy.create_engine("mysql+pymysql://root:" + db_pw + "@" + db_host)
        engine.execute("CREATE DATABASE if not exists timeline CHARACTER SET utf8 COLLATE utf8_general_ci")
        engine.execute("CREATE USER IF NOT EXISTS timeline@'%%' IDENTIFIED BY 'timeline'")
        engine.execute("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, DROP, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON timeline.* TO timeline@'%%'")