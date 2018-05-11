# -*- coding: utf-8 -*-
import socket
from flask_script import Command, prompt, prompt_choices, prompt_pass
from flask_security.forms import RegisterForm
from flask_security.registerable import register_user
from flask_security.utils import get_message
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
        accounts = users.query.filter_by(
            email=email, deployment=deployment).all()
        if not accounts:
            return True, {}

    return False, form.errors


class CreateUserCommand(Command):
    """Create a user"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        username = prompt('Username')
        password = prompt_pass('Password')
        password_confirm = prompt_pass('Confirm Password')

        can_create, form_errors = can_create_user(email, password,
                                                  password_confirm, deployment)

        if can_create:
            try:
                user = register_user(deployment_id=deployment.id, email=email,
                                     password=password, username=username)
            except socket.error as e:
                # if there's an error sending the notification email,
                # recover
                print('Error sending confirmation email: {}'.format(e))
            print('\nUser created successfully')
            print('User(id=%s, email=%s)' % (user.id, user.email))
            return
        print('\nError creating user:')
        for errors in list(form_errors.values()):
            print('\n'.join(errors))


class DeleteUserCommand(Command):
    """Delete a user"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.query.filter_by(
            deployment_id=deployment.id, email=email).one_or_none()
        if not user:
            print('Invalid user')
            return
        users.delete(user)
        print('User deleted successfully')


class ListUsersCommand(Command):
    """List all users"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        for u in users.query.filter_by(deployment_id=deployment.id):
            print('User(id=%s email=%s)' % (u.id, u.email))


class AddUserRoleCommand(Command):
    """Add a role to a user"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.query.filter_by(
            email=email, deployment_id=deployment.id).one_or_none()
        role_name = prompt('Role')
        role = Role.query.filter_by(name=role_name).first()
        if not user:
            print('Invalid user')
            return
        if not role:
            print('Invalid role')
            return
        user.roles.append(role)
        user.save()
        print('Role added to User successfully')


class RemoveUserRoleCommand(Command):
    """Removes a role from a user"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.first(email=email, deployment=deployment)
        role_name = prompt('Role')
        role = Role.objects(name=role_name).first()
        if not user:
            print('Invalid user')
            return
        if not role:
            print('Invalid role')
            return
        user.update(pull_all__roles=[role])
        print('Role removed from User successfully')


class ListUserRolesCommand(Command):
    """List roles a user has"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        email = prompt('Email')
        user = users.query.filter_by(
            email=email, deployment_id=deployment.id).one_or_none()
        if not user:
            print('Invalid user')
            return
        for role in user.roles:
            print('Role(name=%s)' % (role.name))


class ListRolesCommand(Command):
    """List roles"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        for role in Role.query.filter_by(deployment_id=deployment.id).all():
            print('Role(name=%s)' % (role.name))


class AddRoleCommand(Command):
    """Add role"""

    def run(self):
        deployments = Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        role_name = prompt('Role name')
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, deployment_id=deployment.id)
            role.save()
            return
