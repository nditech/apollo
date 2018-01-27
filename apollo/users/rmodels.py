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

    users = db2.relationship(
        'User', back_populates='roles', secondary=roles_users)

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
    roles = db2.relationship(
        'Role', back_populates='users', secondary=roles_users)
