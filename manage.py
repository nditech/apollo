#!/usr/bin/env python
import os
import warnings
from flask.ext.script import Manager, Server, Shell
from flask.ext.security import MongoEngineUserDatastore

from apollo.core import db
from apollo import models, services
from apollo import create_app
from apollo.manage import \
    (CreateUserCommand, DeleteUserCommand, ListUsersCommand,
     AddUserRoleCommand, ListUserRolesCommand, RemoveUserRoleCommand,
     ListRolesCommand, AddRoleCommand,
     AddPermissionToRole, RemovePermissionFromRole, ListPermissionsOfRole,
     CreateDeploymentCommand, ListDeploymentsCommand, CreateEventCommand,
     ListEventsCommand,
     InitializeSubmissionsCommand,
     SetupCommand, MessagePlaybackCommand, EventMigrationCommand)


def read_env(env_path=None):
    if env_path is None:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        warnings.warn('No environment file found. Skipping load.')
        return

    for k, v in parse_env(env_path):
        os.environ.setdefault(k, v)


def parse_env(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip('"').strip("'")
            yield k, v


# load the environment (if found) *before* creating the app
if __name__ == '__main__':
    read_env()

app = create_app()


def _mk_ctx():
    return dict(
        app=app, db=db, models=models, services=services,
        userdatastore=MongoEngineUserDatastore(db, models.User, models.Role))

manager = Manager(app)
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
manager.add_command('migrate_event', EventMigrationCommand())

manager.add_command('init_submissions', InitializeSubmissionsCommand())

manager.add_command('init', SetupCommand())

manager.add_command('playback', MessagePlaybackCommand())

if __name__ == '__main__':
    manager.run()
