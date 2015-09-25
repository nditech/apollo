from apollo.formsframework import FormsService
from apollo.deployments import EventsService
from apollo.locations import (
    SamplesService, LocationTypesService, LocationsService)
from apollo.participants import \
    (ParticipantsService, ParticipantGroupsService, ParticipantRolesService,
        ParticipantPartnersService, ParticipantGroupTypesService)
from apollo.submissions import \
    (SubmissionsService, SubmissionCommentsService, SubmissionVersionsService)
from apollo.users import UsersService, PermsService, UserUploadsService
from apollo.messaging import MessagesService


events = EventsService()
forms = FormsService()
location_types = LocationTypesService()
locations = LocationsService()
participant_partners = ParticipantPartnersService()
participant_roles = ParticipantRolesService()
participants = ParticipantsService()
samples = SamplesService()
submission_comments = SubmissionCommentsService()
submissions = SubmissionsService()
submission_versions = SubmissionVersionsService()
users = UsersService()
perms = PermsService()
user_uploads = UserUploadsService()
messages = MessagesService()
participant_groups = ParticipantGroupsService()
participant_group_types = ParticipantGroupTypesService()
