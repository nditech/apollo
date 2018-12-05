# -*- coding: utf-8 -*-
import calendar
import json

from apollo.dal.serializers import ArchiveSerializer
from apollo.deployments.models import Event
from apollo.formsframework.serializers import FormSetArchiveSerializer
from apollo.locations.serializers import LocationSetArchiveSerializer
from apollo.messaging.serializers import MessageArchiveSerializer
from apollo.participants.serializers import ParticipantSetArchiveSerializer
from apollo.submissions.serializers import SubmissionArchiveSerializer


class EventArchiveSerializer(ArchiveSerializer):
    __model__ = Event

    def deserialize(self, zip_file):
        return super().deserialize(zip_file)

    def serialize(self, event, zip_file):
        with zip_file.open('event.ndjson', 'w') as f:
            data = self.serialize_one(event)
            line = f'{json.dumps(data)}\n'
            f.write(line.encode('utf-8'))

        form_set_serializer = FormSetArchiveSerializer()
        location_set_serializer = LocationSetArchiveSerializer()
        message_serializer = MessageArchiveSerializer()
        participant_set_serializer = ParticipantSetArchiveSerializer()
        submission_serializer = SubmissionArchiveSerializer()

        form_set_serializer.serialize(event, zip_file)
        location_set_serializer.serialize(event, zip_file)
        message_serializer.serialize(event, zip_file)
        participant_set_serializer.serialize(event, zip_file)
        submission_serializer.serialize(event, zip_file)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not of type Event')

        return {
            'name': obj.name,
            'start': calendar.timegm(obj.start.utctimetuple()),
            'end': calendar.timegm(obj.end.utctimetuple()),
            'form_set': obj.form_set.uuid.hex if obj.form_set else None,
            'location_set': obj.location_set.uuid.hex
            if obj.location_set else None,
            'participant_set': obj.participant_set.uuid.hex
            if obj.participant_set else None
        }
