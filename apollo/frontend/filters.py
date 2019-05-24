# -*- coding: utf-8 -*-
from collections import defaultdict

from cgi import escape
from dateutil.parser import parse
from flask_babelex import lazy_gettext as _
from sqlalchemy import or_
from wtforms import widgets, fields, Form
from wtforms.compat import text_type
from wtforms.widgets import html_params, HTMLString
from wtforms_alchemy.fields import QuerySelectField

from apollo import services, models
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.frontend.helpers import get_event
from apollo.helpers import _make_choices
from apollo.submissions.models import FLAG_CHOICES
from apollo.submissions.qa.query_builder import generate_qa_query
from apollo.wtforms_ext import ExtendedSelectField


class EventFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            return queryset.filter(
                models.Submission.event_id == value)
        return queryset


class ChecklistFormFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.forms.find(
                form_type='CHECKLIST'
            ).order_by('name').scalar('id', 'name'), _('Form'))
        super(ChecklistFormFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value):
        if value:
            form = services.forms.get(pk=value)
            return queryset(form=form)
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


class LocationQuerySelectField(QuerySelectField):
    widget = LocationSelectWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.query = models.Location.query.filter(
                models.Location.id == valuelist[0])
        return super(LocationQuerySelectField, self).process_formdata(
            valuelist)


class AJAXLocationFilter(ChoiceFilter):
    field_class = LocationQuerySelectField

    def __init__(self, *args, **kwargs):
        kwargs['query_factory'] = lambda: []
        kwargs['get_pk'] = lambda i: i.id

        return super(AJAXLocationFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value, **kwargs):
        if value:
            location_query = models.Location.query.with_entities(
                models.Location.id
            ).join(
                models.LocationPath,
                models.Location.id == models.LocationPath.descendant_id
            ).filter(models.LocationPath.ancestor_id == value.id)

            return queryset.filter(
                models.Submission.location_id.in_(location_query))

        return queryset


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


class QualityAssuranceFilter(ChoiceFilter):
    field_class = fields.FormField

    def __init__(self, form, qa_form, *args, **kwargs):
        kwargs['form_class'] = form
        self.qa_form = qa_form
        super(QualityAssuranceFilter, self).__init__(*args, **kwargs)

    def queryset_(self, query, value):
        if (
            'criterion' in value and 'condition' in value and
            value['criterion'] and value['condition']
        ):
            try:
                index = int(value['criterion'])
                check = self.qa_form.quality_checks[index]
            except (IndexError, ValueError):
                return query

            qa_expr = '{lvalue} {comparator} {rvalue}'.format(**check)
            qa_subquery = generate_qa_query(qa_expr, self.qa_form)

            if '$location' in qa_expr:
                query = query.join(
                    models.Location,
                    models.Submission.location_id == models.Location.id)

            if '$participant' in qa_expr:
                query = query.join(
                    models.Participant,
                    models.Submission.participant_id == models.Participant.id)

            condition = value['condition']
            if condition == '4':
                # verified
                return query.filter(
                    models.Submission.verification_status == '4')  # noqa
            elif condition == '5':
                # verified
                return query.filter(
                    models.Submission.verification_status == '5')  # noqa
            elif condition == '-1':
                # missing
                return query.filter(qa_subquery == None)  # noqa
            elif condition == '0':
                # OK
                return query.filter(qa_subquery == True)  # noqa
            elif condition == '2':
                # flagged
                return query.filter(qa_subquery == False)  # noqa
        return query


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


class ParticipantIDFilter(CharFilter):
    """This is used to filter on a queryset of submissions.
    """

    def queryset_(self, queryset, value):
        if value:
            participant = models.Participant.query.filter(
                models.Participant.participant_id == value).first()
            if participant is None:
                # this will interfere with the default
                # filtering of master submissions, so
                # return nothing
                return queryset.filter(False)
            return queryset.filter(
                models.Submission.participant_id == participant.id)
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
                timestamp = parse(value, dayfirst=True)
            except Exception:
                return queryset.filter(False)

            upper = timestamp.replace(hour=23, minute=59, second=59)
            lower = timestamp.replace(hour=0, minute=0, second=0)

            return queryset.filter(
                models.Message.received >= lower,
                models.Message.received <= upper
            )

        return queryset


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


def messages_filterset():
    class MessagesFilterSet(FilterSet):
        mobile = MobileFilter()
        text = TextFilter()
        date = DateFilter()
        form_type = MessageSubmissionType()

    return MessagesFilterSet


def dashboard_filterset():
    baseclass = basesubmission_filterset()

    class DashboardFilterSet(baseclass):
        location = AJAXLocationFilter()
        checklist_form = ChecklistFormFilter()

    return DashboardFilterSet


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


def generate_quality_assurance_filter(form):
    quality_check_criteria = [('', _('Quality Check Criterion'))] + \
        (
            [
                (str(idx), qc['description'])
                for idx, qc in enumerate(form.quality_checks)
            ]
            if form.quality_checks else []
        )
    quality_check_conditions = [('', _('Quality Check Condition'))] + \
        list(FLAG_CHOICES)

    class QualityAssuranceConditionsForm(Form):
        criterion = fields.SelectField(choices=quality_check_criteria)
        condition = fields.SelectField(choices=quality_check_conditions)

    attributes = {}

    attributes['quality_check'] = QualityAssuranceFilter(
        QualityAssuranceConditionsForm, form)

    # quarantine status
    attributes['quarantine_status'] = SubmissionQuarantineStatusFilter(
        choices=(
            ('', _('Quarantine Status')),
            ('N', _('Quarantine None')),
            ('A', _('Quarantine All')),
            ('R', _('Quarantine Results'))
        ))

    # participant id and location
    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = AJAXLocationFilter()

    return type(
        'QualityAssuranceFilterSet',
        (basesubmission_filterset(),),
        attributes
    )
