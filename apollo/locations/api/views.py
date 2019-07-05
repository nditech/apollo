# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import or_, text, bindparam
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.deployments.models import Event
from apollo.locations.api.schema import LocationSchema, LocationTypeSchema
from apollo.locations.models import (
    Location, LocationSet, LocationType, LocationTranslations)


@marshal_with(LocationTypeSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class LocationTypeItemResource(MethodResource):
    def get(self, loc_type_id, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if event and event.location_set_id:
            location_set_id = event.location_set_id

        location_type = LocationType.query.join(
            LocationType.location_set
        ).filter(
            LocationType.id == loc_type_id,
            LocationType.location_set_id == location_set_id,
            LocationSet.deployment_id == deployment_id
        ).one()

        return location_type


@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class LocationTypeListResource(BaseListResource):
    schema = LocationTypeSchema()

    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if event and event.location_set_id:
            location_set_id = event.location_set_id

        return LocationType.query.join(
            LocationType.location_set
        ).filter(
            LocationSet.deployment_id == deployment_id,
            LocationSet.id == location_set_id
        )


@marshal_with(LocationSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class LocationItemResource(MethodResource):
    def get(self, location_id, **kwargs):
        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if event and event.location_set_id:
            location_set_id = event.location_set_id

        return Location.query.filter_by(
            id=location_id,
            location_set_id=location_set_id).one()


@use_kwargs(
    {'event_id': fields.Int(), 'q': fields.String()}, locations=['query'])
class LocationListResource(BaseListResource):
    schema = LocationSchema()

    def get_items(self, **kwargs):
        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if event and event.location_set_id:
            location_set_id = event.location_set_id

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
