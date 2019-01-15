# -*- coding: utf-8 -*-
from operator import itemgetter

from flask import g
from flask_babelex import lazy_gettext as _
from sqlalchemy import and_, func, or_
from sqlalchemy.dialects.postgresql import array
from wtforms import widgets

from apollo import models, services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices


class TagLookupFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.contains = kwargs.pop('contains', None)
        super().__init__(*args, **kwargs)

    def filter(self, query, value):
        if value:
            if value == 'NULL':
                condition = models.Submission.data[self.name] == None
            elif value == 'NOT_NULL':
                condition = models.Submission.data[self.name] != None
            else:
                condition = models.Submission.data[self.name] == value

            return query.filter(condition)
        elif self.contains:
            condition = models.Submission.data[self.name] != None
            return query.filter(condition)

        return query


def make_submission_sample_filter(location_set_id):
    class SubmissionSampleFilter(ChoiceFilter):
        def __init__(self, *args, **kwargs):
            sample_choices = services.samples.find(
                location_set_id=location_set_id
            ).with_entities(models.Sample.id, models.Sample.name).all()

            kwargs['choices'] = _make_choices(sample_choices, _('Sample'))
            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                query2 = query.join(
                    models.samples_locations,
                    models.samples_locations.c.location_id == models.Location.id
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

    def filter(self, query, value):
        if value:
            if value == 'NULL':
                return query.filter(
                    models.Submission.incident_status == None)

            return query.filter(
                models.Submission.incident_status == value)

        return query


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
        self.form = kwargs.pop('form')
        self.group = kwargs.pop('group')
        super().__init__(*args, **kwargs)

    def filter(self, query, value):
        group_tags = self.form.get_group_tags(self.group['name'])
        if value == '1':
            # Partial
            return query.filter(
                ~models.Submission.data.has_all(array(group_tags)),
                models.Submission.data.has_any(array(group_tags)))
        elif value == '2':
            # Missing
            return query.filter(or_(
                ~models.Submission.data.has_any(array(group_tags)),
                models.Submission.data == None))    # noqa
        elif value == '3':
            # Complete
            return query.filter(
                models.Submission.data.has_all(array(group_tags)))
        elif value == '4':
            # Conflict
            query_params = [
                models.Submission.conflicts.has_key(tag)    # noqa
                for tag in group_tags
            ]
            return query.filter(or_(*query_params))

        return query


class FieldOptionFilter(ChoiceFilter):
    def filter(self, query, value):
        if value:
            return query.filter(
                models.Submission.data[self.name] == int(value))

        return query


class FieldValueFilter(CharFilter):
    pass


class ParticipantIDFilter(CharFilter):
    def filter(self, query, value):
        if value:
            return query.filter(models.Participant.participant_id == value)

        return query


class SubmissionQuarantineStatusFilter(ChoiceFilter):
    def filter(self, query, value):
        if value and value == 'N':
            return query.filter(or_(
                models.Submission.quarantine_status == None,
                models.Submission.quarantine_status == ''))
        elif value:
            return query.filter_by(quarantine_status=value)

        return query


def make_submission_location_filter(location_set_id):
    class AJAXLocationFilter(CharFilter):
        def __init__(self, *args, **kwargs):
            kwargs['widget'] = widgets.HiddenInput()

            super().__init__(*args, **kwargs)

        def filter(self, query, value):
            if value:
                location_query = models.Location.query.with_entities(
                    models.Location.id
                ).join(
                    models.LocationPath,
                    models.Location.id == models.LocationPath.descendant_id
                ).filter(models.LocationPath.ancestor_id == value)

                return query.filter(
                    models.Submission.location_id.in_(location_query))

            return query

    return AJAXLocationFilter


def make_dashboard_filter(event):
    attributes = {}
    attributes['location'] = make_submission_location_filter(
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
            ('', _('Quarantine Status')),
            ('N', _('Quarantine None')),
            ('A', _('Quarantine All')),
            ('R', _('Quarantine Results'))
        ))

    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = make_submission_location_filter(
        event.location_set_id)()

    return type(
        'SubmissionFilterSet',
        (make_base_submission_filter(event),),
        attributes)
