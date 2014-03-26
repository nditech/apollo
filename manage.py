#!/usr/bin/env python
from flask.ext.script import Manager, Server, Shell
from flask.ext.security import MongoEngineUserDatastore

from apollo.core import db
from apollo import models, services
from apollo.frontend import create_app
from apollo.manage import \
    (CreateUserCommand, DeleteUserCommand, ListUsersCommand)

app = create_app()


def _mk_ctx():
    return dict(
        app=app, db=db, models=models, services=services,
        userdatastore=MongoEngineUserDatastore(db, models.User, models.Role))

manager = Manager(app)
manager.add_command('run', Server())
manager.add_command('shell', Shell(make_context=_mk_ctx))
manager.add_command('createuser', CreateUserCommand())
manager.add_command('deleteuser', DeleteUserCommand())
manager.add_command('listusers', ListUsersCommand())

if __name__ == '__main__':
    manager.run()
