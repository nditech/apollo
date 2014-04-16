from ..core import Service
from .models import Sample, LocationType, Location


class SamplesService(Service):
    __model__ = Sample


class LocationTypesService(Service):
    __model__ = LocationType

    def root(self):
        # a raw query is needed because querying 'normally'
        # (i.e.: ancestors_ref=[]) will raise an exception
        # about an invalid ObjectID
        return self.get(__raw__={'ancestors_ref': []})


class LocationsService(Service):
    __model__ = Location

    def root(self):
        # a raw query is needed because querying 'normally'
        # (i.e.: ancestors_ref=[]) will raise an exception
        # about an invalid ObjectID
        return self.get(__raw__={'ancestors_ref': []})
