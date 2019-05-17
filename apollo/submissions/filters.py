# -*- coding: utf-8 -*-
from operator import itemgetter

from cgi import escape
from flask_babelex import lazy_gettext as _
from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import array
from wtforms import widgets
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString
from wtforms_alchemy.fields import QuerySelectField

from apollo import models, services
from apollo.core import BooleanFilter, CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices


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


def make_submission_sample_filter(location_set_id):
    class SubmissionSampleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            sample_choices = services.samples.find(
                location_set_id=location_set_id
            ).with_entities(models.Sample.id, models.Sample.name).all()

            kwargs['choices'] = _make_choices(sample_choices, _('Sample'))
            super().__init__(*args, **kwargs)

        def queryset_(self, query, value, **kwargs):
            if value:
                query2 = query.join(
                    models.samples_locations,
                    models.samples_locations.c.location_id == models.Location.id    # noqa
                ).join(
                    models.Sample,
                    models.samples_locations.c.sample_id == models.Sample.id
                )
                return query2.filter(models.Sample.id == value)

            return query

    return SubmissionSampleFilter


def make_base_submission_filter(event):
    class BaseSubmissionFilterSet(FilterSet):
        sample = make_submission_sample_filter(event.location_set_id)()

    return BaseSubmissionFilterSet


class IncidentStatusFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = (
            ('', _('Status')),
            ('NULL', _('Unmarked')),
            ('confirmed', _('Confirmed')),
            ('rejected', _('Rejected')),
            ('citizen', _('Citizen Report')),
        )
        super().__init__(*args, **kwargs)

    def filter(self, query, value, **kwargs):
        if value:
            if value == 'NULL':
                return (models.Submission.incident_status == None, None)    # noqa

            return (models.Submission.incident_status == value, None)

        return (None, None)


def make_submission_analysis_filter(event, form):
    attributes = {}
    if form.form_type == 'INCIDENT':
        attributes['status'] = IncidentStatusFilter()

    return type(
        'SubmissionAnalysisFilterSet',
        (make_base_submission_filter(event),),
        attributes
    )


def make_incident_location_filter(event, form, tag):
    base_filter_class = make_submission_analysis_filter(event, form)

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
            constraint = and_(
                    ~models.Submission.data.has_all(array(group_tags)),
                    models.Submission.data.has_any(array(group_tags))
                )
        elif value == '2':
            # Missing
            constraint = or_(
                    ~models.Submission.data.has_any(array(group_tags)),
                    models.Submission.data == None  # noqa
                )
        elif value == '3':
            # Complete
            constraint = models.Submission.data.has_all(array(group_tags))
        elif value == '4':
            # Conflict
            query_params = [
                models.Submission.conflicts.has_key(tag)    # noqa
                for tag in group_tags
            ]
            constraint = or_(*query_params)
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
                models.Submission.data[self.name] == int(value),
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
        elif value:
            return (models.Submission.quarantine_status == value, None)

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
        if valuelist:
            self.query = models.Location.query.filter(
                models.Location.id == valuelist[0])
        return super(LocationQuerySelectField, self).process_formdata(
            valuelist)


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


def make_dashboard_filter(event):
    attributes = {}
    attributes['location'] = make_submission_location_filter(
            event.location_set_id)()
    attributes['sample'] = make_submission_sample_filter(
        event.location_set_id)()

    return type(
        'SubmissionFilterSet',
        (make_base_submission_filter(event),),
        attributes)


def make_submission_list_filter(event, form):
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

    attributes['quarantine_status'] = SubmissionQuarantineStatusFilter(
        choices=(
            ('N', _('Quarantine None')),
            ('A', _('Quarantine All')),
            ('R', _('Quarantine Results'))
        ), default='N')
    attributes['sender_verification'] = SubmissionSenderVerificationFilter(
        choices=(
            ('', _('Sender Verification')),
            ('1', _('Sender Verified')),
            ('2', _('Sender Unverified'))
        ))

    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = make_submission_location_filter(
        event.location_set_id)()
    attributes['conjunction'] = BooleanFilter(
        label=_('Optional Inclusion')
    )
    attributes['online_status'] = OnlineStatusFilter(
        choices=(
            ('', _('Online Status')),
            ('0', _('Online')),
            ('1', _('Offline'))
        )
    )

    return type(
        'SubmissionFilterSet',
        (make_base_submission_filter(event),),
        attributes)
