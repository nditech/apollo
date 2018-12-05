# -*- coding: utf-8 -*-
import calendar
import json

from apollo.dal.serializers import ArchiveSerializer
from apollo.formsframework.models import Form
from apollo.locations.models import Location
from apollo.participants.models import Participant
from apollo.submissions.models import Submission


class SubmissionSerializer(object):
    __model__ = Submission

    def deserialize_one(self, data):
        pass

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not of type Submission')

        return {
            'uuid': obj.uuid.hex,
            'form': obj.form.uuid.hex,
            'participant': obj.participant.uuid.hex
            if obj.participant else None,
            'location': obj.location.uuid.hex,
            'data': obj.data,
            'extra_data': obj.extra_data,
            'submission_type': obj.submission_type.code,
            'created': calendar.timegm(obj.created.utctimetuple()),
            'updated': calendar.timegm(obj.updated.timetuple())
            if obj.updated else None,
            'sender_verified': obj.sender_verified,
            'quarantine_status': obj.quarantine_status.code
            if obj.quarantine_status else '',
            'verification_status': obj.verification_status.code
            if obj.verification_status else '',
            'incident_description': obj.incident_description,
            'incident_status': obj.incident_status.code
            if obj.incident_status else None,
            'overridden_fields': obj.overridden_fields,
        }


class SubmissionArchiveSerializer(ArchiveSerializer):
    def deserialize(self, zip_file):
        return super().deserialize(zip_file)

    def serialize(self, event, zip_file):
        query = Submission.query.filter_by(
            event_id=event.id).join(Form).join(Location).join(Participant)
        serializer = SubmissionSerializer()

        with zip_file.open('submissions.ndjson', 'w') as f:
            for sub in query:
                data = serializer.serialize_one(sub)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))
