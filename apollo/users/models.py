from datetime import datetime
from apollo.core import db
from apollo.deployments.models import Deployment, Event
from flask.ext.security import RoleMixin, UserMixin


class Role(db.Document, RoleMixin):
    name = db.StringField(unique=True)
    description = db.StringField()

    def __unicode__(self):
        return self.name or u''


class User(db.Document, UserMixin):
    email = db.EmailField()
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    current_login_at = db.DateTimeField()
    last_login_at = db.DateTimeField()
    current_login_ip = db.StringField(max_length=45)
    last_login_ip = db.StringField(max_length=45)
    login_count = db.IntField(default=0)
    roles = db.ListField(db.ReferenceField(Role,
                         reverse_delete_rule=db.PULL), default=[])

    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['deployment'],
            ['deployment', 'email'],
            ['deployment', 'email', 'password']
        ]
    }

    def __unicode__(self):
        return self.email or u''


class Need(db.Document):
    '''
    Storage for object permissions in Apollo

    :attr entities: Entities to apply the need to. These are references
    for :class:`apollo.users.models.Role` and :class:`apollo.users.models.
    User` models.
    :attr action: The string containing the action name
    :attr items: (Optional) a list of target object references that this
    permission applies to.
    '''
    entities = db.ListField(db.GenericReferenceField())
    action = db.StringField()
    items = db.ListField(db.GenericReferenceField())

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.action or u''


class UserUpload(db.Document):
    user = db.ReferenceField(User, required=True)
    data = db.FileField()
    event = db.ReferenceField(Event)
    created = db.DateTimeField(default=datetime.utcnow)
