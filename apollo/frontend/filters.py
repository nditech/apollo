from collections import defaultdict
from ..core import CharFilter, ChoiceFilter, FilterSet
from ..helpers import _make_choices
from ..services import events, forms, locations, location_types, samples


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


class DashboardFilter(FilterSet):
    event = EventFilter()
    checklist_form = ChecklistFormFilter()
    sample = SampleFilter()
