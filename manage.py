#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from gevent import monkey

    monkey.patch_all()
except ImportError:
    pass

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Server, Shell
from flask_security import SQLAlchemyUserDatastore

from apollo.core import db
from apollo import models, services
from apollo.manage import \
    (MessagePlaybackCommand, GunicornServer, CeleryWorker, CreateUserCommand)
from apollo.wsgi import application


def _mk_ctx():
    return dict(
        app=application, db=db, models=models, services=services,
        userdatastore=SQLAlchemyUserDatastore(db, models.User, models.Role))


manager = Manager(application)


manager.add_command('run', Server(host='::'))
manager.add_command('shell', Shell(make_context=_mk_ctx))

manager.add_command('playback', MessagePlaybackCommand())

manager.add_command('assets', ManageAssets)
manager.add_command('db', MigrateCommand)
manager.add_command('gunicorn', GunicornServer())
manager.add_command('worker', CeleryWorker())
manager.add_command('create_user', CreateUserCommand())

if __name__ == '__main__':
    manager.run()
