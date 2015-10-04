from os.path import dirname, join, abspath
import re
from datetime import datetime

from jinja2 import Template

from requests.auth import HTTPDigestAuth

from flask.ext.testing import TestCase
from apollo import create_app
from apollo.deployments.models import Deployment, Event
from apollo.formsframework import Form
from apollo.formsframework.models import FormGroup, FormField
from apollo.participants import Participant
from apollo import services
from apollo.submissions import Submission

WWW_AUTHENTICATE = 'WWW-Authenticate'
AUTHORIZATION = 'Authorization'
XFORMS_SUBMISSION_URL = "/xforms/submission"


class MyTest(TestCase):
    def setUp(self):
        Participant.drop_collection()
        Form.drop_collection()
        Event.drop_collection()
        Deployment.drop_collection()
        Submission.drop_collection()
        self.deployment = self.create_deployment()
        self.event = self.create_event()


    def create_deployment(self):
        deployment = Deployment(name="test")
        return deployment.save()

    def create_event(self):
        return services.events.create(deployment=self.deployment, name="test_election", start_date=datetime.strptime("2015-01-01", '%Y-%m-%d'), end_date=datetime.strptime("2015-12-01", '%Y-%m-%d'))

    def create_app(self):
        app = create_app({'TESTING': True, 'SENTRY_DSN': None})
        return app

    def test_submission_view_requires_auth(self):
        response = self.client.post(XFORMS_SUBMISSION_URL)
        self.assertEquals(response.status_code, 401)
        self.assertTrue("Digest" in response.headers.get(WWW_AUTHENTICATE))

    def test_submission_participant_auth_works(self):
        participant = self.create_participant()
        form = self.create_form()
        response = self.client.post(XFORMS_SUBMISSION_URL)
        headers = self.build_auth_request_headers(participant, response)
        test_file_path = join(abspath(dirname(__file__)), 'test_files', 'data.xml')
        test_file_path_generated = join(abspath(dirname(__file__)), 'test_files', 'gen', 'data.xml')
        with open(test_file_path, 'r') as test_file:
            template_text = test_file.read()
            template = Template(template_text)
            xml_data = template.render(form_id=form.id)
            self.write_form_file(test_file_path_generated, xml_data)
            with open(test_file_path_generated, 'r') as generated_file:
                data = {'xml_submission_file': generated_file}
                response = self.client.post(XFORMS_SUBMISSION_URL, headers=headers, data=data)
                self.assertStatus(response, 201)
                submissions = Submission.objects.all()
                self.assertGreater(len(submissions), 1)
                self.assertEqual(submissions[0].contributor, participant)

    def create_form(self):
        form_field = FormField(name="AA", description="The field description")
        form_group = FormGroup(name="startGroup", slug="startGroup", fields=[form_field])
        form = services.forms.create(name="the test form", deployment=self.deployment, events=[self.event], groups=[form_group])
        return form

    def create_participant(self):
        participant = services.participants.create(participant_id="1234", password="the one", deployment=self.deployment, event=self.event)
        return participant

    def write_form_file(self, test_file_path_generated, xml_data):
        with open(test_file_path_generated, 'w') as generated_file:
            generated_file.write(xml_data)

    def build_auth_request_headers(self, participant, response):
        auth_header = response.headers.get(WWW_AUTHENTICATE)
        reg = re.compile('(\w+)[:=][\s"]?([^",]+)"?')
        challenge = dict(reg.findall(auth_header))
        a = HTTPDigestAuth(participant.participant_id, participant.password)
        a.chal = challenge
        auth_header = a.build_digest_header('POST', XFORMS_SUBMISSION_URL)
        headers = {AUTHORIZATION: auth_header}
        return headers
