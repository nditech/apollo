# -*- coding: utf-8 -*-
from collections import OrderedDict

from flask_babelex import lazy_gettext as _
from wtforms.widgets import HiddenInput

from apollo import services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices
from apollo.locations.models import Location, Sample, samples_locations
from apollo.participants import models
from apollo.wtforms_ext import ExtendedMultipleSelectField


class ParticipantIDFilter(CharFilter):
    def filter(self, query, value):
        if value:
            return query.filter_by(participant_id=value)

        return query


class ParticipantNameFilter(CharFilter):
    def filter(self, query, value):
        if value:
            return query.filter(
                models.Participant.name.ilike('%{}%'.format(value)))

        return query


def make_participant_role_filter(participant_set_id):
    class ParticipantRoleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            choices = services.participant_roles.find(
                participant_set_id=participant_set_id
            ).with_entities(
                models.ParticipantRole.id, models.ParticipantRole.name).all()

            kwargs['choices'] = _make_choices(choices, _('All roles'))

            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                return query.filter_by(role_id=value)

            return query

    return ParticipantRoleFilter


def make_participant_partner_filter(participant_set_id):
    class ParticipantPartnerFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            choices = services.participant_partners.find(
                participant_set_id=participant_set_id
            ).with_entities(
                models.ParticipantPartner.id,
                models.ParticipantPartner.name).all()

            kwargs['choices'] = _make_choices(choices, _('All partners'))
            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                return query.filter_by(partner_id=value)
            return query

    return ParticipantPartnerFilter


def make_participant_group_filter(participant_set_id):
    class ParticipantGroupFilter(ChoiceFilter):
        field_class = ExtendedMultipleSelectField

        def __init__(self, *args, **kwargs):
            choices = OrderedDict()
            for group_type in services.participant_group_types.find(
                    participant_set_id=participant_set_id
                ).order_by(
                    models.ParticipantGroupType.name):
                for group in services.participant_groups.find(
                    group_type=group_type
                ).order_by(models.ParticipantGroup.name):
                    choices.setdefault(group_type.name, []).append(
                        (group.id, group.name)
                    )

            kwargs['choices'] = [(k, choices[k]) for k in choices]
            kwargs['coerce'] = int
            super(ParticipantGroupFilter, self).__init__(*args, **kwargs)

        def filter(self, query, values):
            if values:
                query2 = query.join(models.groups_participants).join(
                    models.ParticipantGroup)
                return query2.filter(
                    models.Participant.id ==
                        models.groups_participants.c.participant_id,    # noqa
                    models.ParticipantGroup.id ==
                        models.groups_participants.c.group_id,
                    models.ParticipantGroup.id.in_(values)
                )

            return query

    return ParticipantGroupFilter


class ParticipantPhoneFilter(CharFilter):
    def filter(self, query, value):
        if value:
            query2 = query.join(
                models.ParticipantPhone,
                models.Participant.id ==
                    models.ParticipantPhone.participant_id  # noqa
            ).join(
                models.Phone,
                models.Phone.id == models.ParticipantPhone.phone_id
            )

            return query2.filter(models.Phone.number == value)

        return query


def make_participant_sample_filter(location_set_id):
    class ParticipantSampleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            choices = services.samples.find(
                location_set_id=location_set_id
            ).with_entities(
                Sample.id, Sample.name).all()

            kwargs['choices'] = _make_choices(choices, _('Sample'))
            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                query2 = query.join(
                    Location,
                    models.Participant.location_id == Location.id
                ).join(
                    samples_locations,
                    samples_locations.c.location_id == Location.id
                ).join(
                    Sample,
                    samples_locations.c.sample_id == Sample.id
                )

                return query2.filter(Sample.id == value)

            return query

    return ParticipantSampleFilter


def make_participant_location_filter(location_set_id):
    class AJAXLocationFilter(CharFilter):
        def __init__(self, *args, **kwargs):
            kwargs['widget'] = HiddenInput()

            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                return query

            return query

    return AJAXLocationFilter


def participant_filterset(participant_set_id, location_set_id=None):
    attrs = {
        'participant_id': ParticipantIDFilter(),
        'name': ParticipantNameFilter(),
        'phone': ParticipantPhoneFilter(),
        'role': make_participant_role_filter(participant_set_id)(),
        'group': make_participant_group_filter(participant_set_id)(),
        'partner': make_participant_partner_filter(participant_set_id)()
    }

    if location_set_id:
        attrs['location'] = make_participant_location_filter(location_set_id)()
        attrs['sample'] = make_participant_sample_filter(location_set_id)()

    return type('ParticipantFilterSet', (FilterSet,), attrs)
