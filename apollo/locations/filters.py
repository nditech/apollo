# -*- coding: utf-8 -*-
from .models import Location, LocationGroup, LocationType
from flask_babelex import gettext as _

from sqlalchemy import text
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices


class LocationNameFilter(CharFilter):
    def queryset_(self, queryset, value):
        if value:
            return queryset.filter(
                text('translations.value ILIKE :name')).params(
                    name=f'%{value}%')
        return queryset


class LocationTypeFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        location_set_id = kwargs.pop('location_set_id')

        kwargs['choices'] = _make_choices(
            [(i.id, i.name) for i in LocationType.query.filter(
                LocationType.location_set_id == location_set_id)],
            _('All Types')
        )
        super(LocationTypeFilter, self).__init__(*args, **kwargs)

    def queryset_(self, queryset, value):
        if value:
            return queryset.filter(Location.location_type_id == value)
        return queryset


class LocationGroupFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        location_set_id = kwargs.pop('location_set_id')

        group_choices = LocationGroup.query.filter_by(
            location_set_id=location_set_id
        ).order_by(
            LocationGroup.name
        ).with_entities(
            LocationGroup.id, LocationGroup.name
        ).all()
        self.location_set_id = location_set_id

        kwargs['choices'] = _make_choices(group_choices, _('Group'))
        super().__init__(*args, **kwargs)

    def queryset_(self, queryset, value, **kwargs):
        if value:
            return queryset.join(Location.groups).filter(
                Location.location_set_id == self.location_set_id,
                LocationGroup.id == value
            )

        return queryset


def location_filterset(location_set_id):
    class LocationFilterSet(FilterSet):
        name = LocationNameFilter()
        location_type = LocationTypeFilter(location_set_id=location_set_id)
        location_group = LocationGroupFilter(location_set_id=location_set_id)

    return LocationFilterSet
