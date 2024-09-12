# -*- coding: utf-8 -*-
from collections import defaultdict

from cgi import escape
from dateutil.parser import parse
from dateutil.tz import gettz, UTC
from flask_babel import gettext as _
from sqlalchemy import or_
from wtforms import widgets, fields
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString
from wtforms_alchemy.fields import QuerySelectField

from apollo import services, models
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.frontend.helpers import get_event
from apollo.helpers import _make_choices
from apollo.settings import TIMEZONE
from apollo.wtforms_ext import ExtendedSelectField

APP_TZ = gettz(TIMEZONE)


class EventFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            return queryset.filter(
                models.Submission.event_id == value)
        return queryset


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


class SupervisorSelectWidget(widgets.Select):
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


class SupervisorQuerySelectField(QuerySelectField):
    widget = SupervisorSelectWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0] and valuelist[0] != '__None':
            self.query = models.Participant.query.filter(
                models.Participant.id == valuelist[0])
        return super(SupervisorQuerySelectField, self).process_formdata(
            valuelist)


class LocationFilter(ChoiceFilter):
    field_class = ExtendedSelectField

    def __init__(self, *args, **kwargs):
        displayed_location_types = kwargs.pop(
            'queryset',
            services.location_types.find(is_administrative=True)
        ).scalar('name')
        displayed_locations = services.locations.find(
            location_type__in=displayed_location_types
        ).order_by('location_type', 'name') \
            .scalar('id', 'name', 'location_type')

        filter_locations = defaultdict(list)
        for d_loc in displayed_locations:
            filter_locations[d_loc[2]].append(
                # need to convert ObjectId into unicode
                (str(d_loc[0]), d_loc[1])
            )

        # change first choice to ['', ''] and add the data-placeholder
        # attribute to rendering for the field after switching to
        # Select2 for rendering this
        kwargs['choices'] = [['', _('Location')]] + \
            [[k, v] for k, v in list(filter_locations.items())]

        super(LocationFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value):
        if value:
            location = services.locations.get(pk=value)
            return queryset.filter_in(location)
        return queryset


class SampleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.samples.find().with_entities(
                models.Sample.id, models.Sample.name
            ), _('Sample')
        )
        super(SampleFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value):
        if value:
            sample = services.samples.get(pk=value)
            return queryset(
                location__in=services.locations.find(samples=sample))
        return queryset


class DynamicFieldFilter(ChoiceFilter):
    """Enables filtering on a dynamic MongoEngine document field. By default,
    includes checks for non-existence, existence and equality.
    """
    def __init__(self, *args, **kwargs):
        self.contains = kwargs.pop('contains', None)
        super(DynamicFieldFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value):
        if value:
            if value == 'NULL':
                # check that field does not exist
                query_kwargs = {'{}__exists'.format(self.name): False}
            elif value == 'NOT_NULL':
                # check that field exists
                query_kwargs = {'{}__exists'.format(self.name): True}
            else:
                # checking for equality
                query_kwargs = {'{}'.format(self.name): value}
        elif self.contains:
            # same as check for existence
            query_kwargs = {'{}__exists'.format(self.name): True}
        else:
            query_kwargs = {}

        return queryset(**query_kwargs)


class SubmissionQuarantineStatusFilter(ChoiceFilter):
    def queryset_(self, queryset, value):
        if value:
            if value == 'N':
                allowed_statuses = [
                    i[0] for i in [
                        s for s in models.Submission.QUARANTINE_STATUSES
                        if s[0]
                    ]]
                return queryset.filter(
                    ~models.Submission.quarantine_status.in_(allowed_statuses))
            else:
                return queryset.filter(
                    models.Submission.quarantine_status == value)
        return queryset


class MessageSubmissionType(ChoiceFilter):
    field_class = fields.SelectField

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [
            ('', _('Form Type')),
            ('Invalid', _('Invalid')),
        ]
        kwargs['choices'].extend(models.Form.FORM_TYPES)

        super(MessageSubmissionType, self).__init__(*args, **kwargs)

    def queryset_(self, query, value):
        if value:
            if value == 'Invalid':
                return query.filter(
                    models.Message.submission_id == None)   # noqa
            else:
                return query.filter(models.Form.form_type == value)

        return query


class MobileFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            query_val = '%{}%'.format(value)
            return queryset.filter(
                or_(models.Message.sender.ilike(query_val),
                    models.Message.recipient.ilike(query_val))
            )

        return queryset


class TextFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            query_val = '%{}%'.format(value)
            return queryset.filter(models.Message.text.ilike(query_val))

        return queryset


class DateFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            try:
                dt = parse(value, dayfirst=True)
            except Exception:
                return queryset.filter(False)

            dt = dt.replace(tzinfo=APP_TZ)
            upper = dt.replace(hour=23, minute=59, second=59).astimezone(
                UTC).replace(tzinfo=None)
            lower = dt.replace(hour=0, minute=0, second=0).astimezone(
                UTC).replace(tzinfo=None)

            return queryset.filter(
                models.Message.received >= lower,
                models.Message.received <= upper
            )

        return queryset


class OnlineStatusFilter(ChoiceFilter):
    def filter(self, query, value, **kwargs):
        if value and value == '1':
            return (
                models.Submission.unreachable == True,  # noqa
                None
            )
        elif value:
            return (
                models.Submission.unreachable == False,  # noqa
                None
            )

        return (None, None)


def basesubmission_filterset():
    class BaseSubmissionFilterSet(FilterSet):
        event = EventFilter()
        sample = SampleFilter()

        def __init__(self, *args, **kwargs):
            event = kwargs.pop('default_event', get_event())
            super(BaseSubmissionFilterSet, self).__init__(*args, **kwargs)
            self.declared_filters['event'] = EventFilter(
                widget=widgets.HiddenInput(), default=str(event.id))

    return BaseSubmissionFilterSet


#########################
# factory functions
#########################
def generate_submission_analysis_filter(form):
    attributes = {}
    if form.form_type == 'INCIDENT':
        attributes['status'] = DynamicFieldFilter(
            choices=(
                ('', _('Status')), ('NULL', _('Unmarked')),
                ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
                ('citizen', _('Citizen Report')))
        )

    return type(
        'SubmissionAnalysisFilterSet', (
            basesubmission_filterset(),), attributes)
