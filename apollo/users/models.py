from ..core import db
from flask.ext.security import RoleMixin, UserMixin


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
    roles = db.ListField(db.ReferenceField(Role), default=[])
