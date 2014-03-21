from ..core import Service
from .models import Sample, LocationType, Location
from mongoengine import Q


class SamplesService(Service):
    __model__ = Sample


class LocationTypesService(Service):
    __model__ = LocationType


class LocationsService(Service):
    __model__ = Location
