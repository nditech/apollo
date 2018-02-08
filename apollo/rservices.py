# -*- coding: utf-8 -*-
from apollo.deployments.services import EventService
from apollo.formsframework.services import FormService
from apollo.locations.services import (
    LocationService, LocationTypeService, SampleService)
from apollo.messaging.services import MessageService
from apollo.participants.services import ParticipantService
from apollo.submissions.services import SubmissionService
from apollo.users.services import UserService, UserUploadService

events = EventService()
forms = FormService()
locations = LocationService()
location_types = LocationTypeService()
messages = MessageService()
participants = ParticipantService()
samples = SampleService()
submissions = SubmissionService()
users = UserService()
user_uploads = UserUploadService()
