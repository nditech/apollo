# -*- coding: utf-8 -*-
from flask_security import RoleMixin, UserMixin
from sqlachemy.dialects.postgresql import ARRAY
from sqlalchemy_utils import UUIDType

from apollo.core import db2
from apollo.dal.models import BaseModel


roles_users = db2.Table(
    'roles_users',
    db2.Column('user_id', UUIDType, db2.ForeignKey('users.id')),
    db2.Column('role_id', UUIDType, db2.ForeignKey('roles.id')))


class Role(BaseModel, RoleMixin):
    name = db2.Column(db2.String, unique=True)
    description = db2.Column(db2.String)

    users = db2.relationship('User', back_populates='roles',
        secondary=roles_users)

    def __str__(self):
        return self.name or ''


class User(BaseModel, UserMixin):
    deployment_id = db2.Column(UUIDType, db2.ForeignKey('deployments.id'))
    email = db2.Column(db2.String)
    username = db2.Column(db2.String)
    password = db2.Column(db2.String)
    active = db2.Column(db2.Boolean, default=True)
    confirmed_at = db2.Column(db2.DateTime)
    current_login_at = db2.Column(db2.DateTime)
    last_login_at = db2.Column(db2.DateTime)
    current_login_ip = db2.Column(db2.String)
    last_login_ip = db2.Column(db2.String)
    login_count = db2.Column(db2.Integer)

    deployment = db2.relationship('Deployment', back_populates='users')
    roles = db2.relationship('Role', back_populates='users',
        secondary=roles_users)


# from datetime import datetime
# from apollo.core import db
# from apollo.deployments.models import Deployment, Event
# from flask_security import RoleMixin, UserMixin
# 
# 
# class Role(db.Document, RoleMixin):
#     name = db.StringField(unique=True)
#     description = db.StringField()
# 
#     def __str__(self):
#         return self.name or ''
# 
# 
# class User(db.Document, UserMixin):
#     email = db.EmailField()
#     password = db.StringField(max_length=255)
#     active = db.BooleanField(default=True)
#     confirmed_at = db.DateTimeField()
#     current_login_at = db.DateTimeField()
#     last_login_at = db.DateTimeField()
#     current_login_ip = db.StringField(max_length=45)
#     last_login_ip = db.StringField(max_length=45)
#     login_count = db.IntField(default=0)
#     roles = db.ListField(db.ReferenceField(Role,
#                          reverse_delete_rule=db.PULL), default=[])
# 
#     deployment = db.ReferenceField(Deployment)
# 
#     meta = {
#         'indexes': [
#             ['deployment'],
#             ['deployment', 'email'],
#             ['deployment', 'email', 'password']
#         ]
#     }
# 
#     def __str__(self):
#         return self.email or ''
# 
# 
# class Need(db.Document):
#     '''
#     Storage for object permissions in Apollo
# 
#     :attr entities: Entities to apply the need to. These are references
#     for :class:`apollo.users.models.Role` and :class:`apollo.users.models.
#     User` models.
#     :attr action: The string containing the action name
#     :attr items: (Optional) a list of target object references that this
#     permission applies to.
#     '''
#     entities = db.ListField(db.GenericReferenceField())
#     action = db.StringField()
#     items = db.ListField(db.GenericReferenceField())
# 
#     deployment = db.ReferenceField(Deployment)
# 
#     def __str__(self):
#         return self.action or ''
# 
# 
# class UserUpload(db.Document):
#     user = db.ReferenceField(User, required=True)
#     data = db.FileField()
#     event = db.ReferenceField(Event)
#     created = db.DateTimeField(default=datetime.utcnow)
