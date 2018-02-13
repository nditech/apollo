# -*- coding: utf-8 -*-
from apollo.deployments.services import (
    EventService, FormSetService, LocationSetService, ParticipantSetService)
from apollo.formsframework.services import FormService
from apollo.locations.services import (
    LocationService, LocationTypeService, SampleService)
from apollo.messaging.services import MessageService
from apollo.participants.services import (
    ParticipantPartnerService, ParticipantRoleService, ParticipantService)
from apollo.submissions.services import SubmissionService
from apollo.users.services import UserService, UserUploadService

events = EventService()
forms = FormService()
form_sets = FormSetService()
locations = LocationService()
location_sets = LocationSetService()
location_types = LocationTypeService()
messages = MessageService()
participants = ParticipantService()
participant_partners = ParticipantPartnerService()
participant_roles = ParticipantRoleService()
participant_sets = ParticipantSetService()
samples = SampleService()
submissions = SubmissionService()
users = UserService()
user_uploads = UserUploadService()
