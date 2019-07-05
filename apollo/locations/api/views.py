# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import or_, text, bindparam
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.locations.api.schema import LocationSchema, LocationTypeSchema
from apollo.locations.models import (
    Location, LocationSet, LocationType, LocationTranslations)


@marshal_with(LocationTypeSchema)
class LocationTypeItemResource(MethodResource):
    def get(self, loc_type_id):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None
        location_set_id = getattr(g.event, 'location_id_set', None)

        location_type = LocationType.query.join(
            LocationType.location_set
        ).filter(
            LocationType.id == loc_type_id,
            LocationType.location_set_id == location_set_id,
            LocationSet.deployment_id == deployment_id
        ).one()

        return location_type


class LocationTypeListResource(BaseListResource):
    schema = LocationTypeSchema()

    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None
        location_set_id = getattr(g.event, 'location_set_id', None)

        return LocationType.query.join(
            LocationType.location_set
        ).filter(
            LocationSet.deployment_id == deployment_id,
            LocationSet.id == location_set_id
        )


@marshal_with(LocationSchema)
class LocationItemResource(MethodResource):
    def get(self, location_id):
        location_set_id = getattr(g.event, 'location_set_id', None)
        return Location.query.filter_by(
            id=location_id,
            location_set_id=location_set_id).one()


@use_kwargs({'q': fields.String()}, locations=['query'])
class LocationListResource(BaseListResource):
    schema = LocationSchema()

    def get_items(self, **kwargs):
        location_set_id = getattr(g.event, 'location_set_id', None)

        lookup_args = kwargs.get('q')
        queryset = Location.query.select_from(
            Location, LocationTranslations).filter(
                Location.location_set_id == location_set_id)
        if lookup_args:
            queryset = queryset.filter(
                or_(
                    text('translations.value ILIKE :name'),
                    Location.code.ilike(bindparam('code'))
                )
            ).params(name=f'%{lookup_args}%', code=f'{lookup_args}%')

        return queryset
