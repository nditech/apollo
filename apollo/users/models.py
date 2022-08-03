# -*- coding: utf-8 -*-
from flask_babelex import gettext
from flask_security import RoleMixin, UserMixin
from flask_security.utils import hash_password
from sqlalchemy import func

from apollo.core import db
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True))


roles_permissions = db.Table(
    'roles_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey(
        'permission.id', ondelete='CASCADE'), primary_key=True))

users_permissions = db.Table(
    'users_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey(
        'permission.id', ondelete='CASCADE'), primary_key=True))

role_resource_permissions = db.Table(
    'role_resource_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey(
        'role.id', ondelete='CASCADE'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey(
        'resource.resource_id', ondelete='CASCADE'), primary_key=True))

user_resource_permissions = db.Table(
    'user_resource_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey(
        'resource.resource_id', ondelete='CASCADE'), primary_key=True))


class Role(BaseModel, RoleMixin):
    __tablename__ = 'role'
    __table_args__ = (
        db.UniqueConstraint('deployment_id', 'name'),
    )

    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String)
    description = db.Column(db.String)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('roles', cascade='all, delete',
                           passive_deletes=True))
    permissions = db.relationship(
        'Permission', backref='roles', secondary=roles_permissions)

    def __str__(self):
        return self.name or ''

    def get_by_name(self, name):
        return Role.query.filter_by(name=name).one_or_none()


class User(BaseModel, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
            'deployment.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    first_name = db.Column(db.String)
    active = db.Column(db.Boolean, default=True)
    locale = db.Column(db.String)
    confirmed_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    current_login_ip = db.Column(db.String)
    last_login_ip = db.Column(db.String)
    login_count = db.Column(db.Integer)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('users', cascade='all, delete',
                           passive_deletes=True))
    roles = db.relationship(
        'Role', backref='users', secondary=roles_users)
    permissions = db.relationship(
        'Permission', backref='users', secondary=users_permissions)

    def is_admin(self):
        role = Role.query.join(Role.users).filter(
            Role.deployment == self.deployment, Role.name == 'admin',
            Role.users.contains(self)).first()
        return bool(role)

    def set_password(self, new_password):
        self.password = hash_password(new_password)

    @classmethod
    def import_user_list(cls, dataset, deployment_id, task=None):
        from apollo.deployments.models import Deployment
        deployment = Deployment.query.filter_by(id=deployment_id).first()

        total_records = len(dataset)
        warning_records = 0
        processed_records = 0
        error_log = []

        for record in dataset:
            if not (
                    record['username'].strip()
                    and record['email'].strip()
                    and record['role'].strip()
                    and record['password'].strip()):

                warning_records += 1
                error_log.append({
                    'label': 'WARNING',
                    'message': gettext(
                        'Missing required info '
                        '(username, email, role or password). '
                        'Record will be skipped.')
                })
                continue

            user = cls(
                username=record['username'].strip(),
                email=record['email'].strip(),
                deployment_id=deployment_id,
            )
            user.set_password(record['password'].strip())
            user.roles = Role.query.filter(
                func.lower(Role.name) == record['role'].strip().lower()).all()

            # set the locale if it's set and valid
            locale = record['locale'].strip().lower()
            if locale in deployment.locale_codes:
                user.locale = locale

            user.save()
            processed_records += 1

        if task is not None:
            task.update_task_info(
                total_records=total_records,
                warning_records=warning_records,
                processed_records=processed_records,
                error_log=error_log,
            )


class UserUpload(BaseModel):
    __tablename__ = 'user_upload'

    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), nullable=False)
    created = db.Column(db.DateTime, default=current_timestamp)
    upload_filename = db.Column(db.String)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('user_uploads', cascade='all, delete',
                           passive_deletes=True))
    user = db.relationship(
        'User',
        backref=db.backref('uploads', cascade='all, delete',
                           passive_deletes=True))
