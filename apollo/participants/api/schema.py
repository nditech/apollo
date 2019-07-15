# -*- coding: utf-8 -*-
import marshmallow as ma

from apollo.api.schema import BaseModelSchema
from apollo.participants.models import Participant


class ParticipantSchema(BaseModelSchema):
    role = ma.fields.Method('get_role')

    class Meta:
        model = Participant
        fields = ('id', 'name', 'participant_id', 'role')

    def get_role(self, obj):
        return obj.role.name
