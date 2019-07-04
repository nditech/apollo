# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import or_, text, bindparam
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.participants.api.schema import ParticipantSchema
from apollo.participants.models import Participant, ParticipantTranslations


@marshal_with(ParticipantSchema)
class ParticipantItemResource(MethodResource):
    def get(self, participant_id):
        participant_set_id = g.event.participant_set_id
        participant = Participant.query.filter_by(
            id=participant_id,
            participant_set_id=participant_set_id
        ).one()

        return participant


@use_kwargs({'q': fields.String()}, locations=['query'])
class ParticipantListResource(BaseListResource):
    schema = ParticipantSchema()

    def get_items(self, **kwargs):
        participant_set_id = g.event.participant_set_id

        lookup_item = kwargs.get('q')

        queryset = Participant.query.select_from(
            Participant, ParticipantTranslations).filter(
                Participant.participant_set_id == participant_set_id)

        if lookup_item:
            queryset = queryset.filter(
                or_(
                    text('translations.value ILIKE :name'),
                    Participant.participant_id.ilike(bindparam('pid'))
                )
            ).params(name=f'%{lookup_item}%', pid=f'{lookup_item}%')

        return queryset
