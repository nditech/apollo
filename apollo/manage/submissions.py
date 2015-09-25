from flask.ext.script import Command, prompt_choices
from apollo import services, models


class InitializeSubmissionsCommand(Command):
    """Initializes submissions in readiness to accept data"""

    def run(self):
        deployments = models.Deployment.objects()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        deployment = deployments[int(option) - 1]
        events = services.events.find(deployment=deployment)
        option = prompt_choices('Event', [
            (str(i), v) for i, v in enumerate(events, 1)])
        event = events[int(option) - 1]
        roles = services.participant_roles.find(deployment=deployment)
        option = prompt_choices('Role', [
            (str(i), v) for i, v in enumerate(roles, 1)])
        role = roles[int(option) - 1]
        forms = services.forms.find(
            deployment=deployment, events=event, form_type='CHECKLIST')
        option = prompt_choices('Form', [
            (str(i), v) for i, v in enumerate(forms, 1)])
        form = forms[int(option) - 1]
        location_types = services.location_types.find(deployment=deployment)
        option = prompt_choices('Location level', [
            (str(i), v) for i, v in enumerate(location_types, 1)])
        location_type = location_types[int(option) - 1]

        models.Submission.init_submissions(
            deployment, event, form, role, location_type)
