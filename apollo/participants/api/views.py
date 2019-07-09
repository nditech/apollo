# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import or_, text, bindparam
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import login_or_api_key_required
from apollo.deployments.models import Event
from apollo.participants.api.schema import ParticipantSchema
from apollo.participants.models import (
    Participant, ParticipantSet, ParticipantTranslations)


@marshal_with(ParticipantSchema)
class ParticipantItemResource(MethodResource):
    @login_or_api_key_required
    def get(self, participant_id):
        deployment = getattr(g, 'deployment', None)
        event = getattr(g, 'event', None)

        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        if event and event.participant_set_id:
            participant_set_id = event.participant_set_id
        else:
            participant_set_id = None

        participant = Participant.query.join(
            Participant.participant_set
        ).filter(
            ParticipantSet.id == participant_set_id,
            ParticipantSet.deployment_id == deployment_id,
            Participant.id == participant_id,
            Participant.participant_set_id == ParticipantSet.id
        ).one()

        return participant


@use_kwargs(
    {'event_id': fields.Int(), 'q': fields.String()}, locations=['query'])
class ParticipantListResource(BaseListResource):
    schema = ParticipantSchema()

    def get_items(self, **kwargs):
        event_id = kwargs.get('event_id')
        lookup_item = kwargs.get('q')

        deployment = getattr(g, 'deployment', None)
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        if event and event.participant_set_id:
            participant_set_id = event.participant_set_id
        else:
            participant_set_id = None

        queryset = Participant.query.select_from(
            Participant, ParticipantTranslations).join(
                Participant.participant_set
            ).filter(
                Participant.participant_set_id == participant_set_id,
                ParticipantSet.deployment_id == deployment_id,
                ParticipantSet.id == participant_set_id)

        if lookup_item:
            queryset = queryset.filter(
                or_(
                    text('translations.value ILIKE :name'),
                    Participant.participant_id.ilike(bindparam('pid'))
                )
            ).params(name=f'%{lookup_item}%', pid=f'{lookup_item}%')

        return queryset
