# -*- coding: utf-8 -*-
from itertools import chain
from operator import itemgetter

from cgi import escape
from dateutil.parser import parse
from dateutil.tz import gettz, UTC
from flask_babelex import lazy_gettext as _
from sqlalchemy import Integer, and_, false, or_, true
from sqlalchemy.dialects.postgresql import array
from wtforms import widgets
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString
from wtforms_alchemy.fields import QuerySelectField

from apollo import models
from apollo.core import BooleanFilter, CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices
from apollo.settings import TIMEZONE

APP_TZ = gettz(TIMEZONE)


class TagLookupFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.contains = kwargs.pop('contains', None)
        super().__init__(*args, **kwargs)

    def filter(self, query, value, **kwargs):
        if value:
            if value == 'NULL':
                condition = (models.Submission.data[self.name] == None)   # noqa
            elif value == 'NOT_NULL':
                condition = (models.Submission.data[self.name] != None)   # noqa
            else:
                condition = (models.Submission.data[self.name] == value)

            return (condition, None)
        elif self.contains:
            condition = (models.Submission.data[self.name] != None) # noqa
            return (condition, None)

        return (None, None)


def make_submission_sample_filter(
        participant_set_id, filter_on_locations=False):
    class SubmissionSampleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            sample_choices = models.Sample.query.filter_by(
                participant_set_id=participant_set_id
            ).order_by(
                models.Sample.name
            ).with_entities(models.Sample.id, models.Sample.name).all()
            self.participant_set_id = participant_set_id
            self.filter_on_locations = filter_on_locations

            kwargs['choices'] = _make_choices(sample_choices, _('Sample'))
            super().__init__(*args, **kwargs)

        def filter_by_locations(self, query, value):
            joined_classes = [
                mapper.class_ for mapper in query._join_entities]
            if models.Location in joined_classes:
                query1 = query
            else:
                query1 = query.join(models.Submission.location)

            sample_locations = models.Participant.query.filter_by(
                participant_set_id=participant_set_id
            ).join(
                models.Participant.samples
            ).filter(
                models.Sample.participant_set_id == participant_set_id,
                models.Sample.id == value
            ).with_entities(
                models.Participant.location_id
            )

            query2 = query1.filter(
                models.Submission.location_id.in_(sample_locations)
            )
            return query2

        def filter_by_participants(self, query, value):
            participants_in_sample = models.Participant.query.join(
                models.Participant.samples
            ).filter(
                models.Participant.participant_set_id == participant_set_id,
                models.Sample.id == value
            )
            participant_ids = list(
                chain(*participants_in_sample.with_entities(
                    models.Participant.id).all()))
            query2 = query.filter(
                models.Submission.participant_id.in_(participant_ids))

            return query2

        def queryset_(self, query, value, **kwargs):
            if value:
                if self.filter_on_locations:
                    return self.filter_by_locations(query, value)
                else:
                    return self.filter_by_participants(query, value)

            return query

    return SubmissionSampleFilter


def make_base_submission_filter(event, filter_on_locations=False):
    class BaseSubmissionFilterSet(FilterSet):
        sample = make_submission_sample_filter(
            event.participant_set_id,
            filter_on_locations=filter_on_locations
        )()

    return BaseSubmissionFilterSet


class IncidentStatusFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = (
            ('', _('All Incidents')),
            ('NULL', _('Unmarked Incidents')),
            ('confirmed', _('Confirmed Incidents')),
            ('rejected', _('Rejected Incidents')),
            ('citizen', _('Citizen Report Incidents')),
        )
        super().__init__(*args, **kwargs)

    def filter(self, query, value, **kwargs):
        if value:
            if value == 'NULL':
                return (models.Submission.incident_status == None, None)    # noqa

            return (models.Submission.incident_status == value, None)

        return (None, None)


def make_submission_analysis_filter(event, form, filter_on_locations=False):
    attributes = {}
    if form.form_type == 'INCIDENT':
        attributes['status'] = IncidentStatusFilter(default='confirmed')

    return type(
        'SubmissionAnalysisFilterSet',
        (make_base_submission_filter(
            event, filter_on_locations=filter_on_locations),),
        attributes
    )


def make_incident_location_filter(event, form, tag, filter_on_locations=False):
    base_filter_class = make_submission_analysis_filter(
        event, form, filter_on_locations=filter_on_locations)

    attributes = {
        tag: TagLookupFilter(
            choices=(('NOT_NULL', ''),),
            contains=True,
            default='NOT_NULL',
            widget=widgets.HiddenInput()
        )
    }

    return type(
        'CriticalIncidentLocationFilterSet',
        (base_filter_class,),
        attributes)


class FormGroupFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.formobj = kwargs.pop('form')
        self.group = kwargs.pop('group')
        super().__init__(*args, **kwargs)

    def filter(self, query, value, **kwargs):
        group_tags = self.formobj.get_group_tags(self.group['name'])

        if value == '1':
            # Partial
            if group_tags:
                constraint = and_(
                        ~models.Submission.data.has_all(array(group_tags)),
                        models.Submission.data.has_any(array(group_tags))
                    )
            else:
                constraint = false()
        elif value == '2':
            # Missing
            if group_tags:
                constraint = or_(
                        ~models.Submission.data.has_any(array(group_tags)),
                        models.Submission.data == None  # noqa
                    )
            else:
                constraint = true()
        elif value == '3':
            # Complete
            if group_tags:
                constraint = models.Submission.data.has_all(array(group_tags))
            else:
                constraint = false()
        elif value == '4':
            # Conflict
            if group_tags:
                query_params = [
                    models.Submission.conflicts.has_key(tag)    # noqa
                    for tag in group_tags
                ]
                constraint = or_(*query_params)
            else:
                constraint = false()
        else:
            constraint = None

        if constraint is None:
            return (None, None)
        else:
            form_ = kwargs['form']
            if form_.data and form_.data.get('conjunction') is True:
                # OR conjunction
                return (None, constraint)
            else:
                # AND conjunction
                return (constraint, None)


class FieldOptionFilter(ChoiceFilter):
    def filter(self, query, value, **kwargs):
        if value:
            return (
                models.Submission.data[self.name].astext.cast(
                    Integer) == int(value),
                None
            )

        return (None, None)


class FieldValueFilter(CharFilter):
    pass


class ParticipantIDFilter(CharFilter):
    def filter(self, query, value, **kwargs):
        if value:
            return (
                models.Participant.participant_id == value,
                None
            )

        return (None, None)


class SubmissionQuarantineStatusFilter(ChoiceFilter):
    def filter(self, query, value, **kwargs):
        if value and value == 'N':
            return (
                or_(
                    models.Submission.quarantine_status == None,    # noqa
                    models.Submission.quarantine_status == ''),
                None
            )
        elif value in ('A', 'R'):
            return (models.Submission.quarantine_status == value, None)
        elif value == 'AR':
            return (
                or_(
                    models.Submission.quarantine_status == 'A',
                    models.Submission.quarantine_status == 'R'
                ),
                None
            )
        else:
            return (None, None)


class SubmissionSenderVerificationFilter(ChoiceFilter):
    def filter(self, query, value, **kwargs):
        if value and value == '1':
            return (
                models.Submission.sender_verified == True,  # noqa
                None
            )
        elif value:
            return (
                models.Submission.sender_verified == False, # noqa
                None
            )

        return (None, None)


class OnlineStatusFilter(ChoiceFilter):
    def filter(self, query, value, **kwargs):
        if value and value == '1':
            return (
                models.Submission.unreachable == True,  # noqa
                None
            )
        elif value:
            return (
                models.Submission.unreachable == False, # noqa
                None
            )

        return (None, None)


class DateFilter(CharFilter):
    def filter(self, query, value, **kwargs):
        if value:
            try:
                dt = parse(value, dayfirst=True)
            except (OverflowError, ValueError):
                return (None, None)

            dt = dt.replace(tzinfo=APP_TZ)
            upper_bound = dt.replace(hour=23, minute=59, second=59).astimezone(
                UTC).replace(tzinfo=None)
            lower_bound = dt.replace(hour=0, minute=0, second=0).astimezone(
                UTC).replace(tzinfo=None)

            return (
                and_(
                    models.Submission.participant_updated >= lower_bound,
                    models.Submission.participant_updated <= upper_bound
                ),
                None
            )

        return (None, None)


class LocationSelectWidget(widgets.Select):
    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        if hasattr(label, 'location_type'):
            return HTMLString('<option %s>%s · %s</option>' % (
                html_params(**options),
                escape(text_type(label.name)),
                escape(text_type(label.location_type))))
        else:
            return HTMLString('<option %s>%s</option>' % (
                html_params(**options),
                escape(text_type(label))))


class ParticipantSelectWidget(widgets.Select):
    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        options = dict(kwargs, value=value)
        if selected:
            options['selected'] = True
        if hasattr(label, 'participant_id'):
            return HTMLString('<option %s>%s · %s</option>' % (
                html_params(**options),
                escape(text_type(label.participant_id)),
                escape(text_type(label.name))))
        else:
            return HTMLString('<option %s>%s</option>' % (
                html_params(**options),
                escape(text_type(label))))


class LocationQuerySelectField(QuerySelectField):
    widget = LocationSelectWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] and valuelist[0] != '__None':
            self.query = models.Location.query.filter(
                models.Location.id == valuelist[0])
        return super(LocationQuerySelectField, self).process_formdata(
            valuelist)


class ParticipantQuerySelectField(QuerySelectField):
    widget = ParticipantSelectWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] and valuelist[0] != '__None':
            self.query = models.Participant.query.filter(
                models.Participant.id == valuelist[0])
        return super(ParticipantQuerySelectField, self).process_formdata(
            valuelist)


class FormSerialNumberFilter(CharFilter):
    def filter(self, query, value, **kwargs):
        if value:
            return (
                models.Submission.serial_no == value,
                None
            )

        return (None, None)


def make_submission_location_filter(location_set_id):
    class AJAXLocationFilter(ChoiceFilter):
        field_class = LocationQuerySelectField

        def __init__(self, *args, **kwargs):
            kwargs['query_factory'] = lambda: []
            kwargs['get_pk'] = lambda i: i.id

            super().__init__(*args, **kwargs)

        def queryset_(self, query, value, **kwargs):
            if value:
                location_query = models.Location.query.with_entities(
                    models.Location.id
                ).join(
                    models.LocationPath,
                    models.Location.id == models.LocationPath.descendant_id
                ).filter(models.LocationPath.ancestor_id == value.id)

                return query.filter(
                    models.Submission.location_id.in_(location_query))

            return query

    return AJAXLocationFilter


def make_dashboard_filter(event, filter_on_locations=False):
    attributes = {}
    attributes['location'] = make_submission_location_filter(
            event.location_set_id)()
    attributes['sample'] = make_submission_sample_filter(
        event.participant_set_id, filter_on_locations=filter_on_locations)()

    return type(
        'SubmissionFilterSet',
        (make_base_submission_filter(
            event, filter_on_locations=filter_on_locations),),
        attributes)


def make_submission_list_filter(event, form, filter_on_locations=False):
    attributes = {}
    form._populate_field_cache()

    if form.data and form.data.get('groups'):
        if form.form_type == 'INCIDENT':
            option_fields = [
                f for f in form._field_cache.values()
                if f['type'] == 'select']
            for field in option_fields:
                choices = _make_choices(sorted(
                    ((v, '{} - {}'.format(field['tag'], k)) for k, v in
                        field['options'].items()),
                    key=itemgetter(0)
                ), field['tag'])
                attributes[field['tag']] = FieldOptionFilter(choices=choices)

        for group in form.data.get('groups'):
            field_name = '{}__{}'.format(form.id, group['slug'])
            choices = [
                ('', _('%(group)s Status', group=group['name'])),
                ('1', _('%(group)s Partial', group=group['name'])),
                ('2', _('%(group)s Missing', group=group['name'])),
                ('3', _('%(group)s Complete', group=group['name'])),
                ('4', _('%(group)s Conflict', group=group['name']))
            ]
            attributes[field_name] = FormGroupFilter(
                choices=choices, form=form, group=group)

    if form.form_type == 'INCIDENT':
        attributes['status'] = IncidentStatusFilter()
    elif form.form_type in ['CHECKLIST', 'SURVEY']:
        attributes['quarantine_status'] = SubmissionQuarantineStatusFilter(
            choices=(
                ('', _('Quarantine Status')),
                ('A', _('Quarantine All')),
                ('R', _('Quarantine Results')),
                ('AR', _('Quarantine All + Results')),
                ('N', _('Quarantine None')),
            ), default='')
    attributes['sender_verification'] = SubmissionSenderVerificationFilter(
        choices=(
            ('', _('Phone Confirmation')),
            ('1', _('Phone Confirmed')),
            ('2', _('Phone Unconfirmed'))
        ))

    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = make_submission_location_filter(
        event.location_set_id)()
    attributes['conjunction'] = BooleanFilter(
        label=_('Optional Inclusion')
    )
    attributes['online_status'] = OnlineStatusFilter(
        choices=(
            ('', _('Signal Status')),
            ('0', _('Signal')),
            ('1', _('No Signal'))
        )
    )
    attributes['date'] = DateFilter()
    attributes['fsn'] = FormSerialNumberFilter()

    return type(
        'SubmissionFilterSet',
        (make_base_submission_filter(
            event, filter_on_locations=filter_on_locations),),
        attributes)
