# -*- coding: utf-8 -*-
from flask_security import RoleMixin, UserMixin
from sqlalchemy_utils import UUIDType

from apollo.core import db2
from apollo.dal.models import BaseModel


roles_users = db2.Table(
    'roles_users',
    db2.Column('user_id', db2.Integer, db2.ForeignKey('users.id')),
    db2.Column('role_id', db2.Integer, db2.ForeignKey('roles.id')))


class Role(BaseModel, RoleMixin):
    __tablename__ = 'roles'

    id = db2.Column(db2.Integer, db2.Sequence('role_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    name = db2.Column(db2.String, unique=True)
    description = db2.Column(db2.String)

    deployment = db2.relationship('Deployment', backref='roles')
    users = db2.relationship(
        'User', backref='roles', secondary=roles_users)

    def __str__(self):
        return self.name or ''


class User(BaseModel, UserMixin):
    __tablename__ = 'users'
    id = db2.Column(db2.Integer, db2.Sequence('user_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
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

    deployment = db2.relationship('Deployment', backref='users')
    roles = db2.relationship(
        'Role', backref='users', secondary=roles_users)


class RolePermission(BaseModel):
    __tablename__ = 'role_permissions'

    role_id = db2.Column(
        db2.Integer, db2.ForeignKey('roles.id'), nullable=False,
        primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class UserPermission(BaseModel):
    __tablename__ = 'user_permissions'

    user_id = db2.Column(
        db2.Integer, db2.ForeignKey('users.id'), nullable=False,
        primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class RoleResourcePermission(BaseModel):
    __tablename__ = 'role_resource_permissions'

    role_id = db2.Column(
        db2.Integer, db2.ForeignKey('roles.id'), primary_key=True)
    resource_id = db2.Column(
        db2.Integer, db2.ForeignKey('resources.resource_id'), primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class UserResourcePermission(BaseModel):
    __tablename__ = 'user_resource_permissions'

    user_id = db2.Column(
        db2.Integer, db2.ForeignKey('users.id'), primary_key=True)
    resource_id = db2.Column(
        db2.Integer, db2.ForeignKey('resources.resource_id'), primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)
