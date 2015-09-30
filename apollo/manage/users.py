import socket
from flask.ext.script import Command, prompt, prompt_choices, prompt_pass
from flask.ext.security.forms import RegisterForm
from flask.ext.security.registerable import register_user
from flask.ext.security.utils import get_message
from werkzeug.datastructures import MultiDict

from apollo.services import users
from apollo.models import Deployment, Role


def can_create_user(email, password, password_confirm, deployment):
    data = MultiDict(dict(email=email, password=password,
                     password_confirm=password_confirm))
    form = RegisterForm(data, csrf_enabled=False)

    if form.validate():
        return True, {}

    email_errors = form.errors.get('email', [])
    if (len(email_errors) == 1) and \
        (email_errors[0] ==
            get_message('EMAIL_ALREADY_ASSOCIATED', email=email)[0]):
        accounts = users.find(email=email, deployment=deployment)
        if not accounts:
            return True, {}

    return False, form.errors


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

        can_create, form_errors = can_create_user(email, password,
                                                  password_confirm, deployment)

        if can_create:
            try:
                user = register_user(email=email, password=password)
            except socket.error as e:
                # if there's an error sending the notification email,
                # recover
                print 'Error sending confirmation email: {}'.format(e)
                user = users.get(email=email, deployment=None)
            user.update(set__deployment=deployment)
            print '\nUser created successfully'
            print 'User(id=%s email=%s)' % (user.id, user.email)
            return
        print '\nError creating user:'
        for errors in form_errors.values():
            print '\n'.join(errors)


class DeleteUserCommand(Command):
    """Delete a user"""

    def run(self):
        deployments = Deployment.objects
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.first(deployment=deployment, email=email)
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
