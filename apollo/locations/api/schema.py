# -*- coding: utf-8 -*-
import marshmallow as ma

from apollo.api.schema import BaseModelSchema
from apollo.locations.models import Location, LocationType


class LocationSchema(BaseModelSchema):
    location_type = ma.fields.Method('get_location_type')

    class Meta:
        model = Location
        fields = ('id', 'name', 'location_type', 'code',)

    def get_location_type(self, obj):
        return obj.location_type.name


class LocationTypeSchema(BaseModelSchema):
    class Meta:
        model = LocationType
        fields = ('id', 'name')
