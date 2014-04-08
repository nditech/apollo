from datetime import datetime
from ..core import db
from ..deployments.models import Deployment
from flask.ext.security import RoleMixin, UserMixin


class Role(db.Document, RoleMixin):
    name = db.StringField(unique=True)
    description = db.StringField()

    def __unicode__(self):
        return self.name


class User(db.Document, UserMixin):
    email = db.EmailField()
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirnmed_at = db.DateTimeField()
    current_login_at = db.DateTimeField()
    last_login_at = db.DateTimeField()
    current_login_ip = db.StringField(max_length=24)
    last_login_ip = db.StringField(max_length=24)
    login_count = db.IntField(default=0)
    roles = db.ListField(db.ReferenceField(Role,
                         reverse_delete_rule=db.PULL), default=[])

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.email


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

    def __unicode__(self):
        return self.action


class UserUpload(db.Document):
    user = db.ReferenceField(User, required=True)
    data = db.FileField()
    created = db.DateTimeField(default=datetime.utcnow())
