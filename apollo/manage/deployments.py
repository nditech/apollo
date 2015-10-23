from datetime import datetime
from bson.json_util import dumps, loads
from flask.ext.script import Command, prompt, prompt_choices
from apollo import models


class CreateDeploymentCommand(Command):

    """Create a deployment"""

    def run(self):
        name = prompt('Name')
        hostname = prompt('Hostname')

        try:
            deployment = models.Deployment.objects.get(name=name)
        except models.Deployment.DoesNotExist:
            deployment = models.Deployment(name=name).save()

        deployment.update(add_to_set__hostnames=hostname.strip())

        # create permissions
        models.Need.objects.create(action='view_events', deployment=deployment)
        models.Need.objects.create(
            action='view_participants', deployment=deployment)
        models.Need.objects.create(
            action='view_messages', deployment=deployment)
        models.Need.objects.create(
            action='view_process_analysis', deployment=deployment)
        models.Need.objects.create(
            action='view_result_analysis', deployment=deployment)
        models.Need.objects.create(action='view_forms', deployment=deployment)

        models.Need.objects.create(
            action='add_submission', deployment=deployment)

        models.Need.objects.create(action='edit_forms', deployment=deployment)
        models.Need.objects.create(
            action='edit_locations', deployment=deployment)
        models.Need.objects.create(
            action='edit_participant', deployment=deployment)
        models.Need.objects.create(
            action='edit_submission', deployment=deployment)
        models.Need.objects.create(
            action='edit_both_submissions', deployment=deployment)
        models.Need.objects.create(
            action='edit_submission_quarantine_status', deployment=deployment)

        models.Need.objects.create(
            action='import_participants', deployment=deployment)
        models.Need.objects.create(
            action='import_locations', deployment=deployment)

        models.Need.objects.create(
            action='export_participants', deployment=deployment)
        models.Need.objects.create(
            action='export_messages', deployment=deployment)
        models.Need.objects.create(
            action='export_submissions', deployment=deployment)
        models.Need.objects.create(
            action='export_locations', deployment=deployment)

        models.Need.objects.create(
            action='send_messages', deployment=deployment)


class ListDeploymentsCommand(Command):

    """List deployments"""

    def run(self):
        deployments = models.Deployment.objects.all()
        for deployment in deployments:
            print deployment.name


class CreateEventCommand(Command):

    """Create an event"""

    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
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

        event, _ = models.Event.objects.get_or_create(
            name=name,
            deployment=deployment)
        event.start_date = datetime.combine(start, datetime.min.time())
        event.end_date = datetime.combine(end, datetime.max.time())
        event.save()


class ListEventsCommand(Command):

    """List events in a deployment"""

    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        events = models.Event.objects(deployment=deployment)
        for event in events:
            print event.name


class EventMigrationCommand(Command):
    '''Allows a user to migrate data from one event to another'''
    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]

        events = models.Event.objects(deployment=deployment)
        option = prompt_choices('Source event', [
            (str(i), v) for i, v in enumerate(events, 1)])
        source_event = events[int(option) - 1]

        reduced_events = events(pk__ne=source_event.pk)
        option = prompt_choices('Destination event', [
            (str(i), v) for i, v in enumerate(reduced_events, 1)])
        dest_event = reduced_events[int(option) - 1]

        print '--- AVAILABLE FORMS ---'
        forms = models.Form.objects(deployment=deployment)
        for i, f in enumerate(forms, 1):
            print '{} [{}]'.format(f.name, i)

        form_indexes = raw_input('Enter forms to copy, separated by commas: ')
        indexes = [
            int(i.strip()) for i in form_indexes.split(',')
            if i.strip().isdigit()]

        copy_participants = False
        while True:
            response = raw_input(
                'Copy participants from source to destination (yes/no)? ')
            response = response.lower()
            if response[0] == 'y':
                copy_participants = True
                break
            elif response[0] == 'n':
                break

        for index in indexes:
            form = forms[index - 1]
            data = loads(form.to_json())
            data.pop('_id')
            new_form = models.Form.from_json(dumps(data))
            new_form.events = [dest_event]
            new_form.save()
            form.update(pull__events=dest_event)

        # copy participant data
        if copy_participants:
            participants = models.Participant.objects(
                deployment=deployment, event=source_event)
            supervisor_map = {
                p.participant_id: p.supervisor.participant_id
                for p in participants if p.supervisor}
            for participant in participants:
                data = loads(participant.to_json())
                data.pop('_id')
                data.pop('supervisor', None)
                new_participant = models.Participant.from_json(dumps(data))
                new_participant.accurate_message_count = 0
                new_participant.message_count = 0
                new_participant.event = dest_event
                new_participant.save()

            for p_id, sup_id in supervisor_map.iteritems():
                participant = models.Participant.objects.get(
                    deployment=deployment, event=dest_event,
                    participant_id=p_id)
                supervisor = models.Participant.objects.get(
                    deployment=deployment, event=dest_event,
                    participant_id=sup_id)
                participant.update(set__supervisor=supervisor)
