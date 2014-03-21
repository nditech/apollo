from ..core import db
from ..deployments.models import Deployment
from flask.ext.security import RoleMixin, UserMixin


class Role(db.Document, RoleMixin):
    name = db.StringField(unique=True)
    description = db.StringField()

    deployment = db.ReferenceField(Deployment)

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
    roles = db.ListField(db.ReferenceField(Role), default=[])

    deployment = db.ReferenceField(Deployment)
