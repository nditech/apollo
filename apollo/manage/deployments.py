from datetime import datetime
from flask.ext.script import Command, prompt, prompt_choices
from .. import models


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
