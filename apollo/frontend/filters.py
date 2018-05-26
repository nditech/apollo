# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict

from dateutil.parser import parse
from flask_babelex import lazy_gettext as _
from sqlalchemy import or_
from wtforms import widgets, fields, Form

from apollo import services, models
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.frontend.helpers import get_event
from apollo.helpers import _make_choices
from apollo.submissions.models import FLAG_CHOICES
from apollo.submissions.qa.query_builder import generate_qa_query
from apollo.wtforms_ext import ExtendedSelectField, ExtendedMultipleSelectField


class EventFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset.filter_by(event_id=value)
        return queryset


class ChecklistFormFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.forms.find(
                form_type='CHECKLIST'
            ).order_by('name').scalar('id', 'name'), _('Form'))
        super(ChecklistFormFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            form = services.forms.get(pk=value)
            return queryset(form=form)
        return queryset


class AJAXLocationFilter(CharFilter):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = widgets.HiddenInput()
        return super(AJAXLocationFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            location = services.locations.get(pk=value)
            return queryset.filter_in(location)
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

    def filter(self, queryset, value):
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

    def filter(self, queryset, value):
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

    def filter(self, queryset, value):
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

    def filter(self, query, value):
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

            condition = value['condition']
            if condition == '4':
                # verified
                return query.filter(models.Submission.verification_status == '4')
            elif condition == '5':
                # verified
                return query.filter(models.Submission.verification_status == '5')
            elif condition == '-1':
                # missing
                return query.filter(qa_subquery == None)
            elif condition == '0':
                # OK
                return query.filter(qa_subquery == True)
            elif condition == '2':
                # flagged
                return query.filter(qa_subquery == False)
        return query


class SubmissionQuarantineStatusFilter(ChoiceFilter):
    def filter(self, queryset, value):
        if value:
            if value == 'N':
                allowed_statuses = [i[0] for i in [s for s in models.Submission.QUARANTINE_STATUSES if s[0]]]
                return queryset.filter(~models.Submission.quarantine_status.in_(allowed_statuses))
            else:
                return queryset.filter(models.Submission.quarantine_status == value)
        return queryset


class SubmissionVerificationFilter(ChoiceFilter):
    def filter(self, queryset, value):
        if value is not None or value != '':
            return queryset(verification=value)
        return queryset


class PartnerFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.participant_partners.find().with_entities(
                models.ParticipantPartner.id,
                models.ParticipantPartner.name),
            _('All Organizations')
        )
        super(PartnerFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            partner = services.participant_partners.find(id=value).first()
            return queryset.filter_by(partner=partner)
        return queryset


class RoleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.participant_roles.find().with_entities(
                models.ParticipantRole.id, models.ParticipantRole.name),
            _('All Roles')
        )
        super(RoleFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            role = services.participant_roles.find(id=value).first()
            return queryset.filter_by(role=role)
        return queryset


class ParticipantGroupFilter(ChoiceFilter):
    field_class = ExtendedMultipleSelectField

    def __init__(self, *args, **kwargs):
        choices = OrderedDict()
        # for group in services.participant_groups.find():
        #     choices[group.name] = [
        #         ('{}__{}'.format(group.name, tag), tag) for tag in group.tags
        #     ]
        for group_type in services.participant_group_types.find().order_by(
                models.ParticipantGroupType.name):
            for group in services.participant_groups.find(
                group_type=group_type
            ).order_by(models.ParticipantGroup.name):
                choices.setdefault(group_type.name, []).append(
                    (group.id, group.name)
                )
        kwargs['choices'] = [(k, choices[k]) for k in choices]
        super(ParticipantGroupFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, values):
        if values:
            for value in values:
                group = services.participant_groups.get(id=value)

                queryset = queryset.filter_by(participant_groups=group)
        return queryset


class ParticipantFilter(CharFilter):
    """This is used for filtering a queryset of participants.
    """
    def filter(self, queryset, value):
        if value:
            return queryset(participant_id=value)
        return queryset


class ParticipantPhoneFilter(CharFilter):
    """Used for filtering a queryset of participants by phone number."""
    def filter(self, queryset, value):
        if value:
            return queryset(phones__number__startswith=value)
        return queryset


class ParticipantIDFilter(CharFilter):
    """This is used to filter on a queryset of submissions.
    """
    def filter(self, queryset, value):
        if value:
            participant = services.participants.get(participant_id=value)
            if participant is None:
                # this will interfere with the default
                # filtering of master submissions, so
                # return nothing
                return queryset.none()
            return queryset(contributor=participant)
        return queryset


class ParticipantNameFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset(name__icontains=value)
        return queryset


class FieldOptionFilter(ChoiceFilter):
    def filter(self, queryset, value):
        if value:
            return queryset(**{self.name: int(value)})
        return queryset


class SubmissionStatus(ChoiceFilter):
    field_class = fields.SelectMultipleField

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = (
            ('None', _('Unmarked')),
            ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
            ('citizen', _('Citizen Report')))
        super(SubmissionStatus, self).__init__(*args, **kwargs)

    def filter(self, queryset, values):
        if values:
            values = [None if opt == 'None' else opt for opt in values]
            queryset = queryset(status__in=values)
        return queryset


class MobileFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            query_val = '%{}%'.format(value)
            return queryset.filter(
                or_(models.Message.sender.ilike(query_val),
                    models.Message.recipient.ilike(query_val))
            )

        return queryset


class TextFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            query_val = '%{}%'.format(value)
            return queryset.filter(models.Message.text.ilike(query_val))

        return queryset


class DateFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            try:
                timestamp = parse(value, dayfirst=True)
            except Exception:
                return queryset.none()

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

    return MessagesFilterSet


def dashboard_filterset():
    baseclass = basesubmission_filterset()

    class DashboardFilterSet(baseclass):
        location = AJAXLocationFilter()
        checklist_form = ChecklistFormFilter()

    return DashboardFilterSet


def participant_filterset():
    class ParticipantFilterSet(FilterSet):
        participant_id = ParticipantFilter()
        name = ParticipantNameFilter()
        phone = ParticipantPhoneFilter()
        location = AJAXLocationFilter()
        sample = SampleFilter()
        role = RoleFilter()
        partner = PartnerFilter()
        group = ParticipantGroupFilter()

    return ParticipantFilterSet


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


def generate_critical_incident_location_filter(tag):
    attributes = {}
    attributes[tag] = DynamicFieldFilter(
        choices=(('NOT_NULL', ''),),
        contains=True,
        default='NOT_NULL',
        widget=widgets.HiddenInput()
    )
    attributes['status'] = DynamicFieldFilter(
        choices=(
            ('', _('Status')), ('NULL', _('Unmarked')),
            ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
            ('citizen', _('Citizen Report')))
    )

    return type(
        'CriticalIncidentsLocationFilterSet',
        (basesubmission_filterset(),),
        attributes
    )


def generate_quality_assurance_filter(form):
    quality_check_criteria = [('', _('Quality Check Criterion'))] + \
        [
            (str(idx), qc['description'])
            for idx, qc in enumerate(form.quality_checks)
        ]
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
