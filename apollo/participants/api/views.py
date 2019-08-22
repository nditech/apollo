# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import bindparam, func, or_, text, true
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import login_or_api_key_required
from apollo.deployments.models import Event
from apollo.participants.api.schema import ParticipantSchema
from apollo.participants.models import (
    Participant, ParticipantSet, ParticipantFirstNameTranslations,
    ParticipantFullNameTranslations, ParticipantLastNameTranslations,
    ParticipantOtherNamesTranslations)


@marshal_with(ParticipantSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class ParticipantItemResource(MethodResource):
    @login_or_api_key_required
    def get(self, participant_id, **kwargs):
        deployment = getattr(g, 'deployment', None)
        event = getattr(g, 'event', None)

        event_id = kwargs.get('event_id')
        if event_id:
            event = Event.query.filter_by(id=event_id).first_or_404()

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
        ).first_or_404()

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

        full_name_lat_query = ParticipantFullNameTranslations.lateral(
            'full_name')
        first_name_lat_query = ParticipantFirstNameTranslations.lateral(
            'first_name')
        other_names_lat_query = ParticipantOtherNamesTranslations.lateral(
            'other_names')
        last_name_lat_query = ParticipantLastNameTranslations.lateral(
            'last_name')

        queryset = Participant.query.select_from(
            Participant
        ).join(
            Participant.participant_set
        ).outerjoin(
            full_name_lat_query, true()
        ).outerjoin(
            first_name_lat_query, true()
        ).outerjoin(
            other_names_lat_query, true()
        ).outerjoin(
            last_name_lat_query, true()
        ).filter(
            Participant.participant_set_id == participant_set_id,
            ParticipantSet.deployment_id == deployment_id,
            ParticipantSet.id == participant_set_id)

        if lookup_item:
            queryset = queryset.filter(
                or_(
                    text('full_name.value ILIKE :name'),
                    func.btrim(
                        func.regexp_replace(
                            func.concat_ws(
                                ' ',
                                text('first_name.value'),
                                text('other_names.value'),
                                text('last_name.value'),
                            ), r'\s+', ' ', 'g'
                        )
                    ).ilike(f'%{lookup_item}%'),
                    Participant.participant_id.ilike(bindparam('pid'))
                )
            ).params(name=f'%{lookup_item}%', pid=f'{lookup_item}%')

        return queryset
