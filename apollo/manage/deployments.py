# -*- coding: utf-8 -*-
from datetime import datetime
import socket
from zipfile import ZipFile, ZIP_DEFLATED

from flask_principal import Permission
from flask_script import Command, prompt, prompt_choices, prompt_pass
from flask_security.registerable import register_user
import pytz
from sqlalchemy.dialects.postgresql import array

from apollo import models, settings
from apollo.deployments.serializers import EventArchiveSerializer
from apollo.frontend import permissions


class CreateDeploymentCommand(Command):

    """Create a deployment"""

    def run(self):
        name = prompt('Name')
        hostname = prompt('Hostname')

        deployment = models.Deployment.query.filter_by(
            name=name).one_or_none()

        if not deployment:
            deployment = models.Deployment(
                name=name, hostnames=array([hostname.strip()]))
            deployment.save()

            # create roles
            admin = models.Role(name='admin')
            analyst = models.Role(name='analyst')
            clerk = models.Role(name='clerk')
            manager = models.Role(name='manager')

            admin.deployment_id = deployment.id
            analyst.deployment_id = deployment.id
            clerk.deployment_id = deployment.id
            manager.deployment_id = deployment.id

            admin.save()
            analyst.save()
            clerk.save()
            manager.save()

            # create permissions
            for name in dir(permissions):
                item = getattr(permissions, name, None)
                if isinstance(item, Permission):
                    for need in item.needs:
                        if need.method == 'action':
                            perm = models.Permission(
                                name=need.value, deployment=deployment)
                            perm.save()

            print('Deployment {} created.\n'.format(deployment.name))

            # Create an event
            CreateEventCommand._create_event(deployment)

            # Create an admin user
            email = prompt('Admin user email')
            username = prompt('Admin user username')
            while True:
                password = prompt_pass('Admin user password')
                password2 = prompt_pass('Confirm password')

                if password == password2:
                    break

            try:
                user = register_user(deployment_id=deployment.id, email=email,
                                     password=password, username=username)
            except socket.error:
                pass

            user.roles.append(admin)
            user.save()
            print('User {} created\n'.format(email))

            print('Deployment {} successfully set up\n'.format(
                deployment.name))


class ListDeploymentsCommand(Command):

    """List deployments"""

    def run(self):
        print('Name\t+\tHostnames')
        print('-----\t+\t-----')
        for name, hostnames in models.Deployment.query.with_entities(
                models.Deployment.name, models.Deployment.hostnames):
            print(f'{name}\t+\t{hostnames}')


class CreateEventCommand(Command):

    """Create an event"""

    def run(self):
        deployments = models.Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]

        self._create_event(deployment)

    @staticmethod
    def _create_event(deployment):
        name = prompt('Event name')
        start = end = None
        while True:
            try:
                start = datetime.strptime(
                    prompt('Start date (YYYY-MM-DD)'), '%Y-%m-%d')
            except ValueError:
                pass
            if start:
                break
        while True:
            try:
                end = datetime.strptime(
                    prompt('End date (YYYY-MM-DD)'), '%Y-%m-%d')
            except ValueError:
                pass
            if end:
                break

        # first, set to start and end of the days entered
        start = datetime.combine(start, datetime.min.time())
        end = datetime.combine(end, datetime.max.time())

        # convert to UTC
        app_timezone = pytz.timezone(settings.TIMEZONE)
        start_utc = app_timezone.localize(start).astimezone(
            pytz.UTC)
        end_utc = app_timezone.localize(end).astimezone(
            pytz.UTC)

        event = models.Event(
            name=name,
            deployment_id=deployment.id)
        event.start = start_utc
        event.end = end_utc
        event.save()

        # add role permissions for this event
        roles = models.Role.query.filter_by(deployment=deployment).all()
        event.roles = roles
        event.save()
        print('Event {} created.\n'.format(name))


class ListEventsCommand(Command):

    """List events in a deployment"""

    def run(self):
        print('Event name\t+\tStart\t+\tEnd')
        print('-----\t+\t-----\t+\t-----')
        deployments = models.Deployment.query.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        events = models.Event.query.filter_by(deployment_id=deployment.id)
        for event in events:
            print(f'{event.name}\t+\t{event.start}\t+\t{event.end}')


class ArchiveEventCommand(Command):
    """Archives an event's artifacts"""
    def run(self):
        eas = EventArchiveSerializer()

        # select a deployment
        deployments = models.Deployment.query.all()
        choices = [(str(i), d.name) for i, d in enumerate(deployments, 1)]
        option = prompt_choices('Deployment', choices)
        deployment_id = deployments[int(option) - 1].id

        # select an event in the deployment
        events = models.Event.query.filter_by(
            deployment_id=deployment_id).all()
        choices = [(str(i), ev.name) for i, ev in enumerate(events, 1)]
        option = prompt_choices('Event', choices)
        event = events[int(option) - 1]

        # specify a path to the output archive file
        path = prompt('Path to archive file:')

        # begin
        with ZipFile(path, 'w', ZIP_DEFLATED) as zf:
            eas.serialize(event, zf)

        print('Done')
