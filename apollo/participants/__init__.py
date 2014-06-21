from ..core import Service
from flask import g
from .models import (
    Participant, ParticipantRole, ParticipantPartner, ParticipantGroup,
    ParticipantGroupType
)
import csv
from unidecode import unidecode
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class ParticipantsService(Service):
    __model__ = Participant

    def _set_default_filter_parameters(self, kwargs):
        """Updates the kwargs by setting the default filter parameters
        if available.

        :param kwargs: a dictionary of parameters
        """
        try:
            deployment = kwargs.get('deployment', g.get('deployment'))
            event = kwargs.get('event', g.get('event'))
            if deployment:
                kwargs.update({'deployment': deployment})
            if event:
                kwargs.update({'event': event})
        except RuntimeError:
            pass

        return kwargs

    def export_list(self, queryset):
        headers = [
            u'Participant ID', u'Name', u'Role', u'Partner',
            u'Location ID', u'Supervisor ID', u'Gender', u'Email',
            u'Phone Primary', u'Phone Secondary #1', u'Phone Secondary #2'
        ]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([unidecode(unicode(i)) for i in headers])
        yield output.getvalue()
        output.close()

        for participant in queryset:
            # limit to three numbers for export and pad if less than three
            phone_numbers = [i.number for i in participant.phones][:3]
            phone_numbers += [''] * (3 - len(phone_numbers))

            record = [
                participant.participant_id,
                participant.name,
                participant.role.name,
                participant.partner.name if participant.partner else '',
                participant.location.code if participant.location else '',
                participant.supervisor.participant_id if participant.supervisor
                else '',
                participant.gender,
                participant.email,
            ]

            record.extend(phone_numbers)

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([unidecode(unicode(i)) for i in record])
            yield output.getvalue()
            output.close()

    def export_performance_list(self, queryset):
        headers = [
            'Participant ID', 'Name', 'Role', 'Partner',
            'Phone Primary', 'Phone Secondary #1', 'Phone Secondary #2',
            'Messages Sent', 'Accuracy', 'Completion'
        ]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        yield output.getvalue()
        output.close()

        for participant in queryset:
            # limit to three numbers for export and pad if less than three
            phone_numbers = [i.number for i in participant.phones][:3]
            phone_numbers += [''] * (3 - len(phone_numbers))

            record = [
                participant.participant_id,
                participant.name,
                participant.role.name,
                participant.partner.name if participant.partner else '',
            ]

            record.extend(phone_numbers)
            record.append(participant.message_count)
            try:
                accuracy = (float(participant.accurate_message_count or 0) /
                            participant.message_count)
            except ZeroDivisionError:
                accuracy = 1

            record.append(accuracy)
            record.append(participant.completion_rating)

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([unidecode(unicode(i)) for i in record])
            yield output.getvalue()
            output.close()


class ParticipantRolesService(Service):
    __model__ = ParticipantRole


class ParticipantPartnersService(Service):
    __model__ = ParticipantPartner


class ParticipantGroupsService(Service):
    __model__ = ParticipantGroup


class ParticipantGroupTypesService(Service):
    __model__ = ParticipantGroupType
