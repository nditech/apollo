from __future__ import unicode_literals
from datetime import datetime
from hashlib import sha1
import hmac
import uuid
from mongoengine import DateTimeField, Document, ReferenceField, StringField
from altauth.documents import User


class ApiToken(Document):
    key = StringField(required=True)
    user = ReferenceField(User, required=True)
    created = DateTimeField(default=datetime.utcnow())

    def __unicode__(self):
        return self.key

    def generate_key(self):
        uid = uuid.uuid4()
        return hmac.new(uid.bytes, digestmod=sha1).hexdigest()

    def save(self, *args, **kwargs):
        if not self.key:
           self.key = self.generate_key()
        return super(ApiToken, self).save(*args, **kwargs)
