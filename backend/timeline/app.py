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

import flask
from flask_cors import CORS
from timeline.api.util import to_bool
from timeline.domain import Album, Status
from timeline.extensions import db, celery, cache, migrate
from timeline.api import views, assets, admin, inspect, albums
import logging
import pymysql
import numpy
from logging.handlers import RotatingFileHandler
from flask import Flask
import sqlalchemy
from flask import Blueprint

def create_app(testing=False, cli=False, env=None):
    """Application factory, used to create application"""
    app = Flask(__name__)
          
    app.config.from_object("timeline.config")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config['APPLICATION_ROOT'] = '/timeline'
    if env:
        app.config.from_pyfile(env)
    print(f"Application config for environment {app.config['ENV']}")
    print(f"SQLALCHEMY_DATABASE_URI={app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"TESTING={app.config['TESTING']}")
    print(f"DEBUG={app.config['DEBUG']}")
    print(f"CREATE_DATABASE={app.config['CREATE_DATABASE']}")
    # app.config['SQLALCHEMY_ECHO'] = True

    if testing is True:
        app.config["TESTING"] = True
    if to_bool(app.config.get("FLASK_CORS")):
        print("Activating CORS for Developer purposes")
        cors = CORS(app)
    
    configure_extensions(app, cli)
    register_blueprints(app)
    
    @app.route('/')
    def index():
        return flask.render_template("index.html")

    return app


def prepare_for_tests(app):
    create_for_tests = app.config["TESTING"] or False
    if create_for_tests:
        db.create_all(app=app)
        # from .manage import init
        # init()
        with app.app_context():
            status = Status.query.first()
            if not status:
                status = Status()
                status.next_import_is_new = True
                status.sections_dirty = False
                status.computing_sections = False
                status.num_assets_created = False

                album = Album()
                album.name = "Last Import"
                status.last_import_album = album

                db.session.add(status)  

                status.sections_dirty = False
                status.computing_sections = False

                db.session.commit()
                

def configure_extensions(app, cli):
    """configure flask extensions
    """

    pymysql.converters.encoders[numpy.float64] = pymysql.converters.escape_float
    pymysql.converters.conversions = pymysql.converters.encoders.copy()
    pymysql.converters.conversions.update(pymysql.converters.decoders)

    create_db(app)
    db.init_app(app)
    migrate.init_app(app, db)
    prepare_for_tests(app)

    celery.init_app(app)
    cache.init_app(app)


def register_blueprints(app):
    """register all blueprints for application
    """
    prefix = app.config['APPLICATION_ROOT']
    root = Blueprint('root', __name__, url_prefix=prefix)
    root.register_blueprint(views.blueprint)
    root.register_blueprint(assets.blueprint)
    root.register_blueprint(admin.blueprint)
    root.register_blueprint(inspect.blueprint)
    root.register_blueprint(albums.blueprint)
    app.register_blueprint(root)

#def init_celery(app=None):
#    app = app or create_app()
#    # celery.conf.update(app.config.get("CELERY", {}))
#    # celery.conf.update(result_backend=timeline.config.CELERY_RESULT_BACKEND, broker_url=timeline.config.CELERY_RESULT_BACKEND)
#    class ContextTask(celery.Task):
#        """Make celery tasks work with Flask app context"""
#
#        def __call__(self, *args, **kwargs):
#            with app.app_context():
#                return self.run(*args, **kwargs)
#
#    celery.Task = ContextTask
#    return celery


def setup_logging(package, app, logfile_name):
    log_path = app.config["LOG_PATH"]
    logger = logging.getLogger(package)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)15s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(log_path + '/' + logfile_name, maxBytes=10**7, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_db(app):
    create = app.config["CREATE_DATABASE"]
    if to_bool(create):
        db_host = app.config["DB_HOST"]
        db_pw = app.config["DB_SUPER_USER"]
        engine = sqlalchemy.create_engine("mysql+pymysql://root:" + db_pw + "@" + db_host)
        engine.execute("CREATE DATABASE if not exists timeline CHARACTER SET utf8 COLLATE utf8_general_ci")
        engine.execute("CREATE USER IF NOT EXISTS timeline@'%%' IDENTIFIED BY 'timeline'")
        engine.execute("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, DROP, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON timeline.* TO timeline@'%%'")

    