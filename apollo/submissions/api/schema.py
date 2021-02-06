# -*- coding: utf-8 -*-
import marshmallow as ma

from apollo.api.schema import BaseModelSchema
from apollo.submissions.models import Submission


class LocationSchema(ma.Schema):
    latitude = ma.fields.Float(required=True)
    longitude = ma.fields.Float(required=True)


class SubmissionSchema(BaseModelSchema):
    incident_status = ma.fields.Method('get_incident_status')
    submission_type = ma.fields.Method('get_submission_type')
    location = ma.fields.Nested(LocationSchema)

    class Meta:
        model = Submission
        fields = ('id', 'form_id', 'participant_id', 'location_id', 'data',
                  'submission_type', 'created', 'updated',
                  'incident_description', 'incident_status',
                  'last_phone_number')

    def get_incident_status(self, obj):
        return obj.incident_status.code

    def get_submission_type(self, obj):
        return obj.submission_type.code
