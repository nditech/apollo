# -*- coding: utf-8 -*-
import calendar
import json

from apollo.dal.serializers import ArchiveSerializer
from apollo.messaging.models import Message
from apollo.participants.models import Participant
from apollo.submissions.models import Submission


class MessageSerializer(object):
    __model__ = Message

    def deserialize_one(self, data):
        kwargs = data.copy()

        if data['participant']:
            participant_id = Participant.query.filter_by(
                uuid=data['participant']
            ).with_entities(Participant.id).scalar()
        else:
            participant_id = None

        if data['submission']:
            submission_id = Submission.query.filter_by(
                uuid=data['submission']
            ).with_entities(Submission.id).scalar()
        else:
            submission_id = None

        kwargs.pop('participant')
        kwargs.pop('submission')
        kwargs['participant_id'] = participant_id
        kwargs['submission_id'] = submission_id

        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not of type Message')

        return {
            'direction': obj.direction.code,
            'recipient': obj.recipient,
            'sender': obj.sender,
            'text': obj.text,
            'received': calendar.timegm(obj.received.utctimetuple()),
            'delivered': calendar.timegm(obj.delivered.utctimetuple())
            if obj.delivered else None,
            'submission': obj.submission.uuid.hex
            if obj.submission else None,
            'participant': obj.participant.uuid.hex
            if obj.participant else None,
            'message_type': obj.message_type.code,
            'originating_message': obj.originating_message.uuid.hex
            if obj.originating_message else None
        }


class MessageArchiveSerializer(ArchiveSerializer):
    def deserialize(self, zip_file):
        return super().deserialize(zip_file)

    def serialize(self, event, zip_file):
        with zip_file.open('messages.ndjson', 'w') as f:
            serializer = MessageSerializer()

            for message in event.messages:
                data = serializer.serialize_one(message)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))
