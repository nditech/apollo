from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices
from apollo.submissions.models import FLAG_CHOICES
from apollo.wtforms_ext import ExtendedSelectField, ExtendedMultipleSelectField
from apollo.frontend.helpers import get_event
from collections import defaultdict, OrderedDict
from dateutil.parser import parse
from flask.ext.babel import lazy_gettext as _
from mongoengine import Q
from apollo import services, models
from wtforms import widgets, fields, Form


class EventFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            event = services.events.get(pk=value)
            return queryset(event=event)
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
                (unicode(d_loc[0]), d_loc[1])
            )

        # change first choice to ['', ''] and add the data-placeholder
        # attribute to rendering for the field after switching to
        # Select2 for rendering this
        kwargs['choices'] = [['', _('Location')]] + \
            [[k, v] for k, v in filter_locations.items()]

        super(LocationFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            location = services.locations.get(pk=value)
            return queryset.filter_in(location)
        return queryset


class SampleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.samples.find().scalar('id', 'name'), _('Sample')
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

    def __init__(self, form, *args, **kwargs):
        kwargs['form_class'] = form
        super(QualityAssuranceFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if (
            'criterion' in value and 'condition' in value and
            value['criterion'] and value['condition']
        ):
            if value['condition'] == '-1':
                query_kwargs = {
                    'quality_checks__{}__exists'.format(
                        value['criterion']): False}
            elif value['condition'] == '4':
                query_kwargs = {
                    'verification_status': '4'}
            elif value['condition'] == '5':
                query_kwargs = {
                    'verification_status': '5'}
            else:
                query_kwargs = {'quality_checks__{}'.format(
                    value['criterion']): value['condition'],
                    'verification_status__nin': ['4', '5']}
            return queryset(**query_kwargs)
        return queryset


class SubmissionQuarantineStatusFilter(ChoiceFilter):
    def filter(self, queryset, value):
        if value:
            if value == 'N':
                query_kwargs = {
                    'quarantine_status__nin': map(
                        lambda i: i[0],
                        filter(
                            lambda s: s[0],
                            models.Submission.QUARANTINE_STATUSES))}
            else:
                query_kwargs = {'quarantine_status': value}
            return queryset(**query_kwargs)
        return queryset


class SubmissionVerificationFilter(ChoiceFilter):
    def filter(self, queryset, value):
        if value is not None or value != '':
            return queryset(verification=value)
        return queryset


class PartnerFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.participant_partners.find().scalar('id', 'name'),
            _('All Organizations')
        )
        super(PartnerFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            partner = services.participant_partners.get(pk=value)
            return queryset(partner=partner)
        return queryset


class RoleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.participant_roles.find().scalar('id', 'name'),
            _('All Roles')
        )
        super(RoleFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            role = services.participant_roles.get(pk=value)
            return queryset(role=role)
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
                'name'):
            for group in services.participant_groups.find(
                group_type=group_type.name
            ).order_by('name'):
                choices.setdefault(group_type.name, []).append(
                    (unicode(group.pk), group.name)
                )
        kwargs['choices'] = [(k, choices[k]) for k in choices]
        super(ParticipantGroupFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, values):
        if values:
            for value in values:
                group = services.participant_groups.get(pk=value)

                queryset = queryset(groups=group)
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


class LocationNameFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset(name__icontains=value)
        return queryset


class LocationTypeFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            services.location_types.find().order_by('ancestor_count').scalar(
                'name', 'name'),
            _('All Types')
        )
        super(LocationTypeFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            return queryset(location_type=value)
        return queryset


class FormGroupFilter(ChoiceFilter):
    """Allows filtering on form groups. Each group should have a name
    of the form <form_pk>__<group_slug>.
    """
    def filter(self, queryset, value):
        if value:
            name_parts = self.name.split('__')
            form = services.forms.get(pk=name_parts[0])
            group = [g.name for g in form.groups if g.slug == name_parts[1]][0]

            params = {}

            if value == '1':
                params = {'completion__{}'.format(group): 'Partial'}
            elif value == '2':
                params = {'completion__{}'.format(group): 'Missing'}
            elif value == '3':
                params = {'completion__{}'.format(group): 'Complete'}
            elif value == '4':
                params = {'completion__{}'.format(group): 'Conflict'}

            return queryset(**params)
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
            values = map(lambda opt: None if opt == 'None' else opt, values)
            queryset = queryset(status__in=values)
        return queryset


class MobileFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset.filter(
                Q(recipient__contains=value) | Q(sender__contains=value)
            )

        return queryset


class TextFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset.filter(text__icontains=value)

        return queryset


class DateFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            try:
                timestamp = parse(value)
            except Exception:
                return queryset.none()

            upper = timestamp.replace(hour=23, minute=59, second=59)
            lower = timestamp.replace(hour=0, minute=0, second=0)

            return queryset.filter(
                received__gte=lower,
                received__lte=upper
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
                widget=widgets.HiddenInput(), default=unicode(event.id))

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


def location_filterset():
    class LocationFilterSet(FilterSet):
        name = LocationNameFilter()
        location_type = LocationTypeFilter()

    return LocationFilterSet


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


def generate_submission_filter(form):
    attributes = {}

    # add in form groups
    for group in form.groups:
        field_name = u'{}__{}'.format(form.pk, group.slug)
        choices = [
            ('0', _('%(group)s Status', group=group.name)),
            ('1', _('%(group)s Partial', group=group.name)),
            ('2', _('%(group)s Missing', group=group.name)),
            ('3', _('%(group)s Complete', group=group.name)),
            ('4', _('%(group)s Conflict', group=group.name))
        ]
        attributes[field_name] = FormGroupFilter(choices=choices)

    # quarantine status
    attributes['quarantine_status'] = SubmissionQuarantineStatusFilter(
        choices=(
            ('', _(u'Quarantine Status')),
            ('N', _(u'Quarantine None')),
            ('A', _(u'Quarantine All')),
            ('R', _(u'Quarantine Results'))
        ))

    # participant id and location
    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = AJAXLocationFilter()

    # and status for incident forms
    if form.form_type == 'INCIDENT':
        attributes['status'] = SubmissionStatus()

    return type(
        'SubmissionFilterSet',
        (basesubmission_filterset(),),
        attributes
    )


def generate_quality_assurance_filter(form):
    quality_check_criteria = [('', _('Quality Check Criterion'))] + \
        [(qc['name'], qc['description']) for qc in form.quality_checks]
    quality_check_conditions = [('', _(u'Quality Check Condition'))] + \
        list(FLAG_CHOICES)

    class QualityAssuranceConditionsForm(Form):
        criterion = fields.SelectField(choices=quality_check_criteria)
        condition = fields.SelectField(choices=quality_check_conditions)

    attributes = {}

    attributes['quality_check'] = QualityAssuranceFilter(
        QualityAssuranceConditionsForm)

    # quarantine status
    attributes['quarantine_status'] = SubmissionQuarantineStatusFilter(
        choices=(
            ('', _(u'Quarantine Status')),
            ('N', _(u'Quarantine None')),
            ('A', _(u'Quarantine All')),
            ('R', _(u'Quarantine Results'))
        ))

    # participant id and location
    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = AJAXLocationFilter()

    return type(
        'QualityAssuranceFilterSet',
        (basesubmission_filterset(),),
        attributes
    )
