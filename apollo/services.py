from .formsframework import FormsService
from .deployments import EventsService
from .locations import SamplesService, LocationTypesService, LocationsService
from .participants import \
    (ParticipantsService, ParticipantRolesService, ParticipantPartnersService)
from .submissions import \
    (SubmissionsService, SubmissionVersionsService, SubmissionCommentsService)
from .users import UsersService, PermsService

events = EventsService()
forms = FormsService()
location_types = LocationTypesService()
locations = LocationsService()
participant_partners = ParticipantPartnersService()
participant_roles = ParticipantRolesService()
participants = ParticipantsService()
samples = SamplesService()
submission_comments = SubmissionCommentsService()
submission_versions = SubmissionVersionsService()
submissions = SubmissionsService()
users = UsersService()
perms = PermsService()
