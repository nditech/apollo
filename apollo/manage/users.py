from flask.ext.script import Command, prompt, prompt_choices, prompt_pass
from flask.ext.security.forms import RegisterForm
from flask.ext.security.registerable import register_user
from werkzeug.datastructures import MultiDict

from ..services import users
from ..models import Deployment, Role


class CreateUserCommand(Command):
    """Create a user"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        password = prompt_pass('Password')
        password_confirm = prompt_pass('Confirm Password')
        data = MultiDict(dict(email=email, password=password,
                         password_confirm=password_confirm))
        form = RegisterForm(data, csrf_enabled=False)
        if form.validate():
            user = register_user(email=email, password=password)
            user.update(set__deployment=deployment)
            print '\nUser created successfully'
            print 'User(id=%s email=%s)' % (user.id, user.email)
            return
        print '\nError creating user:'
        for errors in form.errors.values():
            print '\n'.join(errors)


class DeleteUserCommand(Command):
    """Delete a user"""

    def run(self):
        email = prompt('Email')
        user = users.first(email=email)
        if not user:
            print 'Invalid user'
            return
        users.delete(user)
        print 'User deleted successfully'


class ListUsersCommand(Command):
    """List all users"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        for u in users.find(deployment=deployment):
            print 'User(id=%s email=%s)' % (u.id, u.email)


class AddUserRoleCommand(Command):
    """Add a role to a user"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.first(email=email, deployment=deployment)
        role_name = prompt('Role')
        role = Role.objects(name=role_name).first()
        if not user:
            print 'Invalid user'
            return
        if not role:
            print 'Invalid role'
            return
        user.update(add_to_set__roles=role)
        print 'Role added to User successfully'


class RemoveUserRoleCommand(Command):
    """Removes a role from a user"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.first(email=email, deployment=deployment)
        role_name = prompt('Role')
        role = Role.objects(name=role_name).first()
        if not user:
            print 'Invalid user'
            return
        if not role:
            print 'Invalid role'
            return
        user.update(pull_all__roles=[role])
        print 'Role removed from User successfully'


class ListUserRolesCommand(Command):
    """List roles a user has"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.first(email=email, deployment=deployment)
        if not user:
            print 'Invalid user'
            return
        for role in user.roles:
            print 'Role(name=%s)' % (role.name)


class ListRolesCommand(Command):
    """List roles"""

    def run(self):
        for role in Role.objects.all():
            print 'Role(name=%s)' % (role.name)


class AddRoleCommand(Command):
    """Add role"""

    def run(self):
        role_name = prompt('Role name')
        role = Role.objects(name=role_name).first()
        if not role:
            role = Role(name=role_name)
            role.save()
            return
