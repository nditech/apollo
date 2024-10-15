# -*- coding: utf-8 -*-
from html import escape

from flask_babel import gettext as _
from markupsafe import Markup
from sqlalchemy import func, or_, text, true
from wtforms import widgets
from wtforms.widgets import html_params
from wtforms_alchemy.fields import QuerySelectField

from apollo import models, services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices
from apollo.locations.models import Location, LocationPath

from .models import (
    Participant,
    ParticipantPartner,
    ParticipantRole,
    PhoneContact,
    Sample,
)


class ParticipantIDFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            return query.filter(Participant.participant_id == value)
        return query


class ParticipantNameFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            full_name_query = func.jsonb_each_text(
                Participant.full_name_translations
            ).lateral('full_name_translations')
            first_name_query = func.jsonb_each_text(
                Participant.first_name_translations
            ).lateral('first_name_translations')
            other_names_query = func.jsonb_each_text(
                Participant.other_names_translations
            ).lateral('other_names_translations')
            last_name_query = func.jsonb_each_text(
                Participant.last_name_translations
            ).lateral('last_name_translations')

            subquery = Participant.query.outerjoin(
                full_name_query, true()
            ).outerjoin(
                first_name_query, true()
            ).outerjoin(
                other_names_query, true()
            ).outerjoin(
                last_name_query, true()
            ).filter(
                or_(
                    text('full_name_translations.value ILIKE :name'),
                    func.btrim(
                        func.regexp_replace(
                            func.concat_ws(
                                ' ',
                                text('first_name_translations.value'),
                                text('other_names_translations.value'),
                                text('last_name_translations.value'),
                            ), r'\s+', ' ', 'g'
                        )
                    ).ilike(f'%{value}%')
                )
            ).params(
                name=f'%{value}%'
            ).with_entities(
                Participant.id
            ).subquery()

            return query.join(subquery, subquery.c.id == Participant.id)
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
                return query.filter(
                    models.Participant.role_id == value)

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
                return query.filter(
                    models.Participant.partner_id == value)
            return query

    return ParticipantPartnerFilter


class ParticipantPhoneFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            query2 = query.join(
                PhoneContact, Participant.id == PhoneContact.participant_id)

            return query2.filter(PhoneContact.number.ilike(f'%{value}%'))

        return query


def make_participant_sample_filter(participant_set_id):
    class ParticipantSampleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            choices = Sample.query.filter_by(
                participant_set_id=participant_set_id
            ).with_entities(Sample.id, Sample.name).all()

            kwargs['choices'] = _make_choices(choices, _('Sample'))
            super().__init__(*args, **kwargs)

        def queryset_(self, query, value):
            if value:
                query2 = query.join(Participant.samples)

                return query2.filter(Sample.id == value)

            return query

    return ParticipantSampleFilter


class LocationSelectWidget(widgets.Select):
    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        return Markup('<option %s>%s · %s</option>' % (
            html_params(**options),
            escape(str(label.name)),
            escape(str(label.location_type))))


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
        'partner': make_participant_partner_filter(participant_set_id)()
    }

    if location_set_id:
        attrs['location'] = make_participant_location_filter(location_set_id)()
        attrs['sample'] = make_participant_sample_filter(participant_set_id)()

    return type('ParticipantFilterSet', (FilterSet,), attrs)
