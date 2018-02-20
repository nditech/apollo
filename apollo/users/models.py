# -*- coding: utf-8 -*-
from flask_security import RoleMixin, UserMixin

from apollo.core import db
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True))


class Role(BaseModel, RoleMixin):
    __tablename__ = 'role'
    __table_args__ = (
        db.UniqueConstraint('deployment_id', 'name'),
    )

    id = db.Column(db.Integer, db.Sequence('role_id_seq'), primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String)
    description = db.Column(db.String)

    deployment = db.relationship('Deployment', backref='roles')

    def __str__(self):
        return self.name or ''

    def get_by_name(self, name):
        return Role.query.filter_by(name=name).one_or_none()


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    current_login_ip = db.Column(db.String)
    last_login_ip = db.Column(db.String)
    login_count = db.Column(db.Integer)

    deployment = db.relationship('Deployment', backref='users')
    roles = db.relationship(
        'Role', backref='users', secondary=roles_users)

    def is_admin(self):
        role = Role.query.join(Role.users).filter(
            Role.deployment == self.deployment, Role.name == 'admin',
            Role.users.contains(self)).first()
        return bool(role)


class RolePermission(BaseModel):
    __tablename__ = 'role_permission'

    role_id = db.Column(db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    perm_name = db.Column(db.String, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String)
    deployment = db.relationship('Deployment', backref='role_permissions')
    role = db.relationship('Role', backref='role_permissions')


class UserPermission(BaseModel):
    __tablename__ = 'user_permission'

    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    perm_name = db.Column(db.String, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String)
    deployment = db.relationship('Deployment', backref='user_permissions')
    user = db.relationship('User', backref='user_permissions')


class RoleResourcePermission(BaseModel):
    __tablename__ = 'role_resource_permission'

    role_id = db.Column(db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey(
        'resource.resource_id', ondelete='CASCADE'), primary_key=True)
    perm_name = db.Column(db.String, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String)
    deployment = db.relationship(
        'Deployment', backref='role_resource_permissions')
    role = db.relationship('Role', backref='role_resource_permissions')


class UserResourcePermission(BaseModel):
    __tablename__ = 'user_resource_permission'

    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey(
        'resource.resource_id', ondelete='CASCADE'), primary_key=True)
    perm_name = db.Column(db.String, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String)
    deployment = db.relationship(
        'Deployment', backref='user_resource_permissions')
    user = db.relationship('User', backref='user_resource_permissions')


class UserUpload(BaseModel):
    __tablename__ = 'user_upload'

    id = db.Column(
        db.Integer, db.Sequence('user_upload_id_seq'), primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id',ondelete='CASCADE'), nullable=False)
    created = db.Column(db.DateTime, default=current_timestamp)
    upload_filename = db.Column(db.String)
    deployment = db.relationship('Deployment', backref='user_uploads')
    user = db.relationship('User', backref='uploads')
