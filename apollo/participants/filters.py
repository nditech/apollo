# -*- coding: utf-8 -*-
from collections import OrderedDict
from sqlalchemy import text

from cgi import escape
from flask_babelex import lazy_gettext as _
from wtforms import widgets
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString
from wtforms_alchemy.fields import QuerySelectField

from apollo import models, services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices
from apollo.locations.models import (
    Location, LocationPath, Sample, samples_locations)
from apollo.wtforms_ext import ExtendedMultipleSelectField

from .models import Participant, ParticipantRole, ParticipantPartner
from .models import ParticipantGroup, ParticipantGroupType, groups_participants
from .models import Phone, ParticipantPhone


class ParticipantIDFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            return query.filter(Participant.participant_id == value)
        return query


class ParticipantNameFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            return query.filter(
                text('translations.value ILIKE :name')).params(
                    name=f'%{value}%')
        return query


def make_participant_role_filter(participant_set_id):
    class ParticipantRoleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            choices = services.participant_roles.find(
                participant_set_id=participant_set_id
            ).with_entities(
                ParticipantRole.id, ParticipantRole.name).all()

            kwargs['choices'] = _make_choices(choices, _('All Roles'))

            super().__init__(*args, **kwargs)

        def queryset_(self, query, value):
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
                ParticipantPartner.id,
                ParticipantPartner.name).all()

            kwargs['choices'] = _make_choices(choices, _('All Organizations'))
            super().__init__(*args, **kwargs)

        def queryset_(self, query, value):
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
                    ParticipantGroupType.name):
                for group in services.participant_groups.find(
                    group_type=group_type
                ).order_by(ParticipantGroup.name):
                    choices.setdefault(group_type.name, []).append(
                        (group.id, group.name)
                    )

            kwargs['choices'] = [(k, choices[k]) for k in choices]
            kwargs['coerce'] = int
            super(ParticipantGroupFilter, self).__init__(*args, **kwargs)

        def queryset_(self, query, values):
            if values:
                query2 = query.join(groups_participants).join(
                    ParticipantGroup)
                return query2.filter(
                    Participant.id ==
                        models.groups_participants.c.participant_id,    # noqa
                    ParticipantGroup.id ==
                        groups_participants.c.group_id,
                    ParticipantGroup.id.in_(values)
                )

            return query

    return ParticipantGroupFilter


class ParticipantPhoneFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            query2 = query.join(
                ParticipantPhone,
                Participant.id ==
                    ParticipantPhone.participant_id  # noqa
            ).join(
                Phone,
                Phone.id == ParticipantPhone.phone_id
            )

            return query2.filter(Phone.number.ilike(f'%{value}%'))

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

        def queryset_(self, query, value):
            if value:
                query2 = query.join(
                    Location,
                    Participant.location_id == Location.id
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


class LocationSelectWidget(widgets.Select):
    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        return HTMLString('<option %s>%s · %s</option>' % (
            html_params(**options),
            escape(text_type(label.name)),
            escape(text_type(label.location_type))))


class LocationQuerySelectField(QuerySelectField):
    widget = LocationSelectWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.query = models.Location.query.filter(
                models.Location.id == valuelist[0])
        return super(LocationQuerySelectField, self).process_formdata(
            valuelist)


def make_participant_location_filter(location_set_id):
    class AJAXLocationFilter(CharFilter):
        field_class = LocationQuerySelectField

        def __init__(self, *args, **kwargs):
            kwargs['query_factory'] = lambda: []
            kwargs['get_pk'] = lambda i: i.id

            super().__init__(*args, **kwargs)

        def queryset_(self, query, value):
            if value:
                location_query = Location.query.with_entities(
                    Location.id).join(
                    LocationPath, Location.id == LocationPath.descendant_id
                ).filter(LocationPath.ancestor_id == value.id)

                return query.filter(
                    Participant.location_id.in_(location_query))

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
