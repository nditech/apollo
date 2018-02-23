# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _

from apollo import models, services
from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.helpers import _make_choices


class LocationNameFilter(CharFilter):
    def filter(self, queryset, value):
        if value:
            return queryset.filter(models.Location.name.ilike(
                '%{}%'.format(value)))
        return queryset


class LocationTypeFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        location_set_id = kwargs.pop('location_set_id')

        kwargs['choices'] = _make_choices(
            services.location_types.find(
                location_set_id=location_set_id
            ).with_entities(
                models.LocationType.id,
                models.LocationType.name).all(),
            _('All Types')
        )
        super(LocationTypeFilter, self).__init__(*args, **kwargs)

    def filter(self, queryset, value):
        if value:
            return queryset.filter_by(location_type_id=value)
        return queryset


def location_filterset(location_set_id):
    class LocationFilterSet(FilterSet):
        name = LocationNameFilter()
        location_type = LocationTypeFilter(location_set_id=location_set_id)

    return LocationFilterSet
