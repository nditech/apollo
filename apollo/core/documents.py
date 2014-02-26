from __future__ import unicode_literals
from datetime import datetime
from mongoengine import DateTimeField, Document, ObjectIdField
from mongoengine import ReferenceField, SequenceField
from mongoengine import StringField
from altauth.documents import User


class VersionSequenceField(SequenceField):
    def get_sequence_name(self):
        obj_id = self.owner_document.obj
        return '_'.join(('version', 'seq', str(obj_id)))


class SubmissionVersion(Document):
    obj = ObjectIdField(required=True)
    data = StringField(required=True)
    version = VersionSequenceField()
    timestamp = DateTimeField(default=datetime.utcnow())
    changed_by = ReferenceField(User, required=True)

    meta = {
        'ordering': ['-version', '-timestamp']
    }
