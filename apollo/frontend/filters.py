from collections import defaultdict
from flask.ext.babel import lazy_gettext as _
from wtforms import widgets
from .helpers import get_event
from ..core import CharFilter, ChoiceFilter, FilterSet
from ..helpers import _make_choices
from ..services import (
    events, forms, locations, location_types, participants,
    participant_partners, participant_roles, samples)
from ..wtforms_ext import ExtendedSelectField


class EventFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            events.find().scalar('id', 'name'), 'Event')
        super(EventFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            event = events.get(pk=value)
            return queryset(created__gte=event.start_date,
                            created__lte=event.end_date)
        return queryset


class ChecklistFormFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            forms.find(form_type='CHECKLIST').scalar('id', 'name'), 'Form')
        super(ChecklistFormFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            form = forms.get(pk=value)
            return queryset(form=form)
        return queryset


class LocationFilter(ChoiceFilter):
    field_class = ExtendedSelectField

    def __init__(self, *args, **kwargs):
        displayed_location_types = kwargs.pop(
            'queryset',
            location_types.find(on_submissions_view=True)
        ).scalar('name')
        displayed_locations = locations.find(
            location_type__in=displayed_location_types
        ).order_by('location_type', 'name') \
            .scalar('id', 'name', 'location_type')

        filter_locations = defaultdict(list)
        for d_loc in displayed_locations:
            filter_locations[d_loc[2]].append(d_loc[:2])

        kwargs['choices'] = [['', 'Location']] + \
            [[k, v] for k, v in filter_locations.items()]

        super(LocationFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            location = locations.get(pk=value)
            return queryset.filter_in(location)
        return queryset


class SampleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            samples.find().scalar('id', 'name'), 'Sample'
        )
        super(SampleFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            sample = samples.get(pk=value)
            return queryset(location__in=locations.find(samples=sample))
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


class PartnerFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            participant_partners.find().scalar('id', 'name'), 'Partner'
        )
        super(PartnerFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            partner = participant_partners.get(pk=value)
            return queryset(partner=partner)
        return queryset


class RoleFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = _make_choices(
            participant_roles.find().scalar('id', 'name'), 'Role'
        )
        super(RoleFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            role = participant_roles.get(pk=value)
            return queryset(role=role)
        return queryset


class ParticipantFilter(CharFilter):
    """This is used for filtering a queryset of participants.
    """
    def filter(self, queryset, value):
        if value:
            return queryset(participant_id=value)
        return queryset


class ParticipantIDFilter(CharFilter):
    """This is used to filter on a queryset of submissions.
    """
    def filter(self, queryset, value):
        if value:
            participant = participants.find(pk=value)
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
        return value


class FormGroupFilter(ChoiceFilter):
    """Allows filtering on form groups. Each group should have a name
    of the form <form_pk>__<group_slug>.
    """
    def filter(self, queryset, value):
        if value:
            name_parts = self.name.split('_')
            form = forms.get(pk=name_parts[0])
            group = [g.name for g in form.groups if g.slug == name_parts[1]][0]

            params = {}

            if value == '1':
                params = {'completion__{}'.format(group): 'Partial'}
            elif value == '2':
                params = {'completion__{}'.format(group): 'Missing'}
            elif value == '3':
                params = {'completion__{}'.format(group): 'Complete'}

            return queryset(**params)
        return queryset


class BaseSubmissionFilterSet(FilterSet):
    event = EventFilter()
    sample = SampleFilter()

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('default_event', events.default())
        super(BaseSubmissionFilterSet, self).__init__(*args, **kwargs)
        self.declared_filters['event'] = EventFilter(
            widget=widgets.HiddenInput(), default=unicode(event.id))


class DashboardFilterSet(FilterSet):
    sample = SampleFilter()
    event = EventFilter()
    location = LocationFilter()
    checklist_form = ChecklistFormFilter()

    def __init__(self, *args, **kwargs):
        super(DashboardFilterSet, self).__init__(*args, **kwargs)
        self.declared_filters['event'].field.default = get_event()


class ParticipantFilterSet(FilterSet):
    participant_id = ParticipantFilter()
    name = ParticipantNameFilter()
    location = LocationFilter()
    sample = SampleFilter()
    role = RoleFilter()
    partner = PartnerFilter()


#########################
# factory functions
#########################
def generate_submission_analysis_filter(form):
    attributes = {}
    if form.form_type == 'INCIDENT':
        attributes['status'] = DynamicFieldFilter(
            choices=(('', _('Status')), ('NULL', _('Unmarked')),
                    ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
                    ('citizen', _('Citizen Report')))
        )
        attributes['witness'] = DynamicFieldFilter(
            choices=(('', _('Witness')), ('NULL', _('Unspecified')),
                    ('witnessed', _('Witnessed incident')),
                    ('after', _('Arrived after incident')),
                    ('reported', _('Incident was reported')))
        )

    return type(
        'SubmissionAnalysisFilterSet', (BaseSubmissionFilterSet,), attributes)


def generate_critical_incident_location_filter(tag):
    attributes = {}
    attributes[tag] = DynamicFieldFilter(
        choices=(('NOT_NULL', ''),),
        contains=True,
        default='NOT_NULL',
        widget=widgets.HiddenInput()
    )
    attributes['status'] = DynamicFieldFilter(
        choices=(('', _('Status')), ('NULL', _('Unmarked')),
                ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
                ('citizen', _('Citizen Report')))
    )
    attributes['witness'] = DynamicFieldFilter(
        choices=(('', _('Witness')), ('NULL', _('Unspecified')),
                ('witnessed', _('Witnessed incident')),
                ('after', _('Arrived after incident')),
                ('reported', _('Incident was reported')))
    )

    return type(
        'CriticalIncidentsLocationFilterSet',
        (BaseSubmissionFilterSet,),
        attributes
    )


def generate_submission_filter(form):
    attributes = {}

    # add in form groups
    for group in form.groups:
        field_name = '{}__{}'.format(form.pk, group.slug)
        choices = [
            ('0', _('%(group)s Status') % {'group': group.name}),
            ('1', _('%(group)s Partial') % {'group': group.name}),
            ('2', _('%(group)s Missing') % {'group': group.name}),
            ('3', _('%(group)s Complete') % {'group': group.name})
        ]
        attributes[field_name] = FormGroupFilter(choices=choices)

    # participant id and location
    attributes['participant_id'] = ParticipantIDFilter()
    attributes['location'] = LocationFilter()

    # and status for incident forms
    if form.form_type == 'INCIDENT':
        attributes['status'] = DynamicFieldFilter(
            choices=(('', _('Status')), ('NULL', _('Unmarked')),
                    ('confirmed', _('Confirmed')), ('rejected', _('Rejected')),
                    ('citizen', _('Citizen Report')))
        )

    return type(
        'SubmissionFilterSet',
        (BaseSubmissionFilterSet,),
        attributes
    )
