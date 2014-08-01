from .formsframework import FormsService
from .deployments import EventsService
from .locations import SamplesService, LocationTypesService, LocationsService
from .participants import \
    (ParticipantsService, ParticipantGroupsService, ParticipantRolesService,
        ParticipantPartnersService, ParticipantGroupTypesService)
from .submissions import \
    (SubmissionsService, SubmissionCommentsService, SubmissionVersionsService)
from .users import UsersService, PermsService, UserUploadsService
from .messaging import MessagesService, GatewayService


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
gateways = GatewayService()
