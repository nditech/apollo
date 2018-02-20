# -*- coding: utf-8 -*-
from datetime import datetime
from flask_script import Command, prompt, prompt_choices
import pytz
from sqlalchemy.dialects.postgresql import array

from apollo import models, settings


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

            # Create an event
            CreateEventCommand._create_event(deployment)


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


# class EventMigrationCommand(Command):
#     '''Allows a user to migrate data from one event to another'''
#     def run(self):
#         deployments = models.Deployment.objects.all()
#         option = prompt_choices('Deployment', [
#             (str(i), v) for i, v in enumerate(deployments, 1)])
#         deployment = deployments[int(option) - 1]

#         events = models.Event.objects(deployment=deployment)
#         option = prompt_choices('Source event', [
#             (str(i), v) for i, v in enumerate(events, 1)])
#         source_event = events[int(option) - 1]

#         reduced_events = events(pk__ne=source_event.pk)
#         option = prompt_choices('Destination event', [
#             (str(i), v) for i, v in enumerate(reduced_events, 1)])
#         dest_event = reduced_events[int(option) - 1]

#         print('--- AVAILABLE FORMS ---')
#         forms = models.Form.objects(deployment=deployment)
#         for i, f in enumerate(forms, 1):
#             print('{} [{}]'.format(f.name, i))

#         form_indexes = input('Enter forms to copy, separated by commas: ')
#         indexes = [
#             int(i.strip()) for i in form_indexes.split(',')
#             if i.strip().isdigit()]

#         copy_participants = False
#         while True:
#             response = input(
#                 'Copy participants from source to destination (yes/no)? ')
#             response = response.lower()
#             if response[0] == 'y':
#                 copy_participants = True
#                 break
#             elif response[0] == 'n':
#                 break

#         for index in indexes:
#             form = forms[index - 1]
#             data = loads(form.to_json())
#             data.pop('_id')
#             new_form = models.Form.from_json(dumps(data))
#             new_form.events = [dest_event]
#             new_form.save()
#             form.update(pull__events=dest_event)

#         # copy participant data
#         if copy_participants:
#             participants = models.Participant.objects(
#                 deployment=deployment, event=source_event)
#             supervisor_map = {
#                 p.participant_id: p.supervisor.participant_id
#                 for p in participants if p.supervisor}
#             for participant in participants:
#                 data = loads(participant.to_json())
#                 data.pop('_id')
#                 data.pop('supervisor', None)
#                 new_participant = models.Participant.from_json(dumps(data))
#                 new_participant.accurate_message_count = 0
#                 new_participant.message_count = 0
#                 new_participant.event = dest_event
#                 new_participant.save()

#             for p_id, sup_id in supervisor_map.items():
#                 participant = models.Participant.objects.get(
#                     deployment=deployment, event=dest_event,
#                     participant_id=p_id)
#                 supervisor = models.Participant.objects.get(
#                     deployment=deployment, event=dest_event,
#                     participant_id=sup_id)
#                 participant.update(set__supervisor=supervisor)
