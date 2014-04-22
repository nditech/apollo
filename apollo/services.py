from .formsframework import FormsService
from .deployments import EventsService
from .locations import SamplesService, LocationTypesService, LocationsService
from .participants import \
    (ParticipantsService, ParticipantRolesService, ParticipantPartnersService)
from .submissions import \
    (SubmissionsService, SubmissionCommentsService, SubmissionVersionsService)
from .users import UsersService, PermsService, UserUploadsService
from .messaging import MessagesService


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
