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
    (CreateUserCommand, DeleteUserCommand, ListUsersCommand,
     AddUserRoleCommand, ListUserRolesCommand, RemoveUserRoleCommand,
     ListRolesCommand, AddRoleCommand,
     AddPermissionToRole, RemovePermissionFromRole, ListPermissionsOfRole,
     CreateDeploymentCommand, ListDeploymentsCommand, CreateEventCommand,
     ListEventsCommand, ArchiveEventCommand,
     InitializeSubmissionsCommand,
     SetupCommand, MessagePlaybackCommand, GunicornServer, CeleryWorker)
from apollo.wsgi import application


def _mk_ctx():
    return dict(
        app=application, db=db, models=models, services=services,
        userdatastore=SQLAlchemyUserDatastore(db, models.User, models.Role))


manager = Manager(application)


manager.add_command('run', Server(host='::'))
manager.add_command('shell', Shell(make_context=_mk_ctx))

manager.add_command('create_user', CreateUserCommand())
manager.add_command('delete_user', DeleteUserCommand())
manager.add_command('list_users', ListUsersCommand())

manager.add_command('add_userrole', AddUserRoleCommand())
manager.add_command('remove_userrole', RemoveUserRoleCommand())
manager.add_command('list_userroles', ListUserRolesCommand())
manager.add_command('list_roles', ListRolesCommand())
manager.add_command('add_role', AddRoleCommand())

manager.add_command('add_rolepermission', AddPermissionToRole())
manager.add_command('remove_rolepermission', RemovePermissionFromRole())
manager.add_command('list_rolepermissions', ListPermissionsOfRole())

manager.add_command('create_deployment', CreateDeploymentCommand())
manager.add_command('list_deployments', ListDeploymentsCommand())

manager.add_command('create_event', CreateEventCommand())
manager.add_command('list_events', ListEventsCommand())

manager.add_command('init_submissions', InitializeSubmissionsCommand())

manager.add_command('init', SetupCommand())

manager.add_command('playback', MessagePlaybackCommand())

manager.add_command('assets', ManageAssets)
manager.add_command('db', MigrateCommand)
manager.add_command('gunicorn', GunicornServer())
manager.add_command('worker', CeleryWorker())
manager.add_command('archive', ArchiveEventCommand())

if __name__ == '__main__':
    manager.run()
