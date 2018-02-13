# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.locations.models import Location, LocationType, Sample


class LocationService(Service):
    __model__ = Location


class LocationTypeService(Service):
    __model__ = LocationType


class SampleService(Service):
    __model__ = Sample
