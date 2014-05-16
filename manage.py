#!/usr/bin/env python
from flask.ext.script import Manager, Server, Shell
from flask.ext.security import MongoEngineUserDatastore

from apollo.core import db
from apollo import models, services
from apollo.frontend import create_app
from apollo.manage import \
    (CreateUserCommand, DeleteUserCommand, ListUsersCommand,
     AddUserRoleCommand, ListUserRolesCommand, RemoveUserRoleCommand,
     ListRolesCommand, AddRoleCommand,
     AddPermissionToRole, RemovePermissionFromRole, ListPermissionsOfRole,
     CreateDeploymentCommand, ListDeploymentsCommand, CreateEventCommand,
     ListEventsCommand,
     InitializeSubmissionsCommand)

app = create_app()


def _mk_ctx():
    return dict(
        app=app, db=db, models=models, services=services,
        userdatastore=MongoEngineUserDatastore(db, models.User, models.Role))

manager = Manager(app)
manager.add_command('run', Server(host='0.0.0.0'))
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

if __name__ == '__main__':
    manager.run()
