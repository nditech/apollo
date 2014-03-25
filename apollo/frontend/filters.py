from collections import defaultdict
from wtforms import widgets
from ..core import CharFilter, ChoiceFilter, FilterSet
from ..helpers import _make_choices
from ..services import (
    events, forms, locations, location_types, participant_partners,
    participant_roles, samples)
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

        kwargs['choices'] = [['', '']] + \
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


class ParticipantIDFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset(participant_id=value)
        return queryset


class ParticipantNameFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset(name__icontains=value)
        return value


class DashboardFilterSet(FilterSet):
    location = LocationFilter()
    event = EventFilter()
    checklist_form = ChecklistFormFilter()
    sample = SampleFilter()

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('default_event', events.default())
        super(DashboardFilterSet, self).__init__(*args, **kwargs)
        self.declared_filters['event'] = EventFilter(
            widget=widgets.HiddenInput(), default=unicode(event.id))


class ParticipantFilterSet(FilterSet):
    participant_id = ParticipantIDFilter()
    name = ParticipantNameFilter()
    location = LocationFilter()
    sample = SampleFilter()
    role = RoleFilter()
    partner = PartnerFilter()
