#!/usr/bin/env python
from flask.ext.script import Manager, Server

from apollo.frontend import create_app
from apollo.manager import \
    (CreateUserCommand, DeleteUserCommand, ListUsersCommand)

manager = Manager(create_app())
manager.add_command('run', Server())
manager.add_command('createuser', CreateUserCommand())
manager.add_command('deleteuser', DeleteUserCommand())
manager.add_command('listusers', ListUsersCommand())

if __name__ == '__main__':
    manager.run()
