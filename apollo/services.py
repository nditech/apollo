# -*- coding: utf-8 -*-
from apollo.deployments.services import EventService
from apollo.formsframework.services import FormService
from apollo.locations.services import (
    LocationService, LocationSetService, LocationTypeService)
from apollo.messaging.services import MessageService
from apollo.participants.services import (
    ParticipantService, ParticipantGroupService, ParticipantGroupTypeService,
    ParticipantSetService, ParticipantPartnerService, ParticipantRoleService,
    PhoneContactService)
from apollo.submissions.services import (
    SubmissionService, SubmissionCommentService, SubmissionVersionService)
from apollo.users.services import UserService, UserUploadService

events = EventService()
forms = FormService()
locations = LocationService()
location_sets = LocationSetService()
location_types = LocationTypeService()
messages = MessageService()
participants = ParticipantService()
participant_partners = ParticipantPartnerService()
participant_roles = ParticipantRoleService()
participant_sets = ParticipantSetService()
participant_groups = ParticipantGroupService()
participant_group_types = ParticipantGroupTypeService()
phone_contacts = PhoneContactService()
submissions = SubmissionService()
submission_comments = SubmissionCommentService()
submission_versions = SubmissionVersionService()
users = UserService()
user_uploads = UserUploadService()
