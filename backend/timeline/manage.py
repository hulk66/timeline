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
from timeline.domain import Status, Album
from timeline.event_handler import EventHandler
import click
from flask.cli import FlaskGroup, with_appcontext
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from timeline.util.init_things import insert_things, set_hierarchy
from timeline.app import create_app, setup_logging
from flask import current_app
from timeline.tasks.initial_scan import inital_scan
import time


def create_timeline(info):
    return create_app(cli=True)


@click.group(cls=FlaskGroup, create_app=create_timeline)
def cli():
    """Main entry point"""

@cli.command()
@with_appcontext
def watchdog():
    """Start watchdog and perform the initial scan of the directory
    """
    app = create_app()
    setup_logging("timeline", current_app, "watchdog.log")
    click.echo("Starting Watchdog")

    polling = current_app.config.get("POLLING")
    path = current_app.config.get("ASSET_PATH")
    initial_scan = current_app.config.get("INITIAL_SCAN")
    if initial_scan:
        click.echo("Performing Initial Scan")
        inital_scan(path)
        click.echo("Initial Scan done")

    start_watchdog(polling, path)


def start_watchdog(polling, path):
    observer = Observer()
    if polling:
        observer = PollingObserver(timeout=20)
    observer.schedule(EventHandler(path), path=path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



@cli.command("init")
def init():
    """Init Things tables
    """
    from timeline.extensions import db

    click.echo("init things")
    required = insert_things("timeline/resources/class-descriptions.csv")
    click.echo("init thing relationships")
    if required:
        set_hierarchy("timeline/resources/bbox_labels_600_hierarchy.json")
    db.create_all()
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
    click.echo("init done")    

    
if __name__ == "__main__":
    cli()
