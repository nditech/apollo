# -*- coding: utf-8 -*-
from flask_security import RoleMixin, UserMixin

from apollo.core import db2
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp


roles_users = db2.Table(
    'roles_users',
    db2.Column('user_id', db2.Integer, db2.ForeignKey('user.id')),
    db2.Column('role_id', db2.Integer, db2.ForeignKey('role.id')))


class Role(BaseModel, RoleMixin):
    __tablename__ = 'role'

    id = db2.Column(db2.Integer, db2.Sequence('role_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    name = db2.Column(db2.String, unique=True)
    description = db2.Column(db2.String)

    deployment = db2.relationship('Deployment', backref='roles')

    def __str__(self):
        return self.name or ''


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    id = db2.Column(db2.Integer, db2.Sequence('user_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
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
    __tablename__ = 'role_permission'

    role_id = db2.Column(
        db2.Integer, db2.ForeignKey('role.id'), nullable=False,
        primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class UserPermission(BaseModel):
    __tablename__ = 'user_permission'

    user_id = db2.Column(
        db2.Integer, db2.ForeignKey('user.id'), nullable=False,
        primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class RoleResourcePermission(BaseModel):
    __tablename__ = 'role_resource_permission'

    role_id = db2.Column(
        db2.Integer, db2.ForeignKey('role.id'), primary_key=True)
    resource_id = db2.Column(
        db2.Integer, db2.ForeignKey('resource.resource_id'), primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class UserResourcePermission(BaseModel):
    __tablename__ = 'user_resource_permission'

    user_id = db2.Column(
        db2.Integer, db2.ForeignKey('user.id'), primary_key=True)
    resource_id = db2.Column(
        db2.Integer, db2.ForeignKey('resource.resource_id'), primary_key=True)
    perm_name = db2.Column(db2.String, primary_key=True)
    description = db2.Column(db2.String)


class UserUpload(BaseModel):
    __tablename__ = 'user_upload'

    id = db2.Column(
        db2.Integer, db2.Sequence('user_upload_id_seq'), primary_key=True)
    user_id = db2.Column(
        db2.Integer, db2.ForeignKey('user.id'), nullable=False)
    created = db2.Column(db2.DateTime, default=current_timestamp)
    upload_filename = db2.Column(db2.String)
