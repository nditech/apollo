from ..core import db
from flask.ext.security import RoleMixin, UserMixin
from apollo.frontend.models import Deployment


class Role(db.Document, RoleMixin):
    name = db.StringField(unique=True)
    description = db.StringField()
    deployment = db.ReferenceField(Deployment)


class User(db.Document, UserMixin):
    deployment = db.ReferenceField(Deployment)
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
