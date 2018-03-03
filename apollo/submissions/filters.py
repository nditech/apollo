# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from wtforms import widgets

from apollo import models, services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices


class TagLookupFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.contains = kwargs.pop('contains', None)
        super.__init__(*args, **kwargs)

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
                    models.Location,
                    models.Submission.location_id == models.Location.id
                ).join(
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
                return query.filter_by(incident_status=None)

            return query.filter_by(incident_status=value)

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
