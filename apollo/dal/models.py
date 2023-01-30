# -*- coding: utf-8 -*-
'''Base model classes.

The concept of resources and the permissions implementation
is liberally adapted (aka stolen) from the source of ziggurat_foundations
(https://github.com/ergo/ziggurat-foundations)
'''
import warnings
import sqlalchemy as sa
from uuid import uuid4

from flask import g
from flask_babelex import get_locale, gettext as _
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import TranslationHybrid
from sqlalchemy_utils.i18n import cast_locale_expr

from apollo.core import db


def get_default_locale(obj, attr):
    try:
        deployment = g.deployment

        locale = deployment.primary_locale or 'en'
    except AttributeError:
        warnings.warn('No Deployment Set')
        locale = 'en'
    except RuntimeError:
        raise

    if isinstance(obj, db.Model):
        attribute = getattr(obj, attr)
        if attribute is None or attribute == {}:
            return ''

        # checking for the default locale for a model instance
        if locale in attribute.keys():
            return locale
        else:
            try:
                return sorted(attribute.keys())[0]
            except IndexError:
                return ''

    # return default deployment locale
    return locale


def expr_factory(self, attr):
    '''
    The default `expr_factory` method for the TranslationHybrid accessor that
    comes with sqlalchemy_utils expects that every field that uses it should
    have at least a value for the default_locale. In our case, there's no
    guarantee as we do not enforce that.

    In order to mitigate a situation where there's no value for the
    current_locale and that there's also no value for the default_locale, the
    `expr_factory` method is monkey-patched to allow for retrieving the first
    available value if there's no value for either the current_locale or the
    default_locale
    '''
    def expr(cls):
        cls_attr = getattr(cls, attr.key)
        current_locale = cast_locale_expr(cls, self.current_locale, attr)
        default_locale = cast_locale_expr(cls, self.default_locale, attr)
        return sa.func.coalesce(
            cls_attr[current_locale],
            sa.func.coalesce(
                cls_attr[default_locale],
                sa.func.jsonb_path_query_first(cls_attr, '$.*'))
        )
    return expr


TranslationHybrid.expr_factory = expr_factory

translation_hybrid = TranslationHybrid(
    current_locale=get_locale,
    default_locale=get_default_locale
)


class CRUDMixin(object):
    '''CRUD mixin class'''

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    @declared_attr
    def uuid(self):
        return db.Column(UUID(as_uuid=True), default=uuid4, nullable=False)

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()

        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class BaseModel(CRUDMixin, db.Model):
    '''Base model class'''
    __abstract__ = True


class Permission(BaseModel):
    __tablename__ = 'permission'

    # NOTE: please update this list when adding new permissions
    PERMISSION_DESCRIPTIONS = {
        'view_events': _('Users can change events manually'),
        'view_participants': _('Users can view the participant list'),
        'view_messages': _('Users can view the message list'),
        'view_quality_assurance': _(
            'Users can view the quality assurance list'),
        'view_process_analysis': _('Users can view the process data summary'),
        'view_result_analysis': _('Users can view the results data summary'),
        'add_submission': _('Users can create critical incidents'),
        'edit_forms': _('Users can modify forms'),
        'edit_locations': _('Users can edit location data'),
        'edit_submission': _('Users can edit submissions'),
        'edit_both_submissions': _(
            'Users can modify observer and location checklists'),
        'edit_submission_quarantine_status': _(
            'Users can edit checklist quarantine statuses'),
        'edit_submission_verification_status': _(
            'Users can edit checklist verification statuses'),
        'edit_participant': _('Users can edit participant data'),
        'import_participants': _('Users can import participant data'),
        'import_locations': _('Users can import location data'),
        'export_participants': _('Users can export participant data'),
        'export_locations': _('Users can export location data'),
        'export_messages': _('Users can export messages'),
        'export_submissions': _('Users can export submissions'),
        'send_messages': _('Users can send participants messages'),
        'modify_images': _('Users can delete or replace submission images'),
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    deployment = db.relationship(
        'Deployment', backref=db.backref('permissions', cascade='all, delete'))

    def __str__(self):
        return self.__class__.PERMISSION_DESCRIPTIONS.get(self.name, self.name)


class ResourceMixin(object):
    '''
    Resource mixin class. Any resources to be protected should inherit from
    the concrete class, `Resource`, not this one.
    Still a SQLA newbie, but if this were the concrete class, SQLA would
    scream bloody murder, so I'm copying the author of ziggurat_foundations
    and making this a mixin class.
    '''
    @declared_attr
    def __tablename__(self):
        return 'resource'

    @declared_attr
    def resource_id(self):
        return db.Column(
            db.Integer, autoincrement=True, nullable=False, primary_key=True)

    @declared_attr
    def resource_type(self):
        return db.Column(db.String, nullable=False)

    @declared_attr
    def deployment_id(self):
        return db.Column(
            db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
            nullable=False)

    @declared_attr
    def deployment(self):
        return db.relationship(
            'Deployment',
            backref=db.backref('resources', cascade='all, delete',
                               passive_deletes=True))

    @declared_attr
    def roles(self):
        return db.relationship(
            'Role', backref='resources', secondary='role_resource_permissions')

    @declared_attr
    def users(self):
        return db.relationship(
            'User', backref='resources', secondary='user_resource_permissions')

    __mapper_args__ = {'polymorphic_on': resource_type}


class Resource(ResourceMixin, BaseModel):
    '''
    Concrete resource class. Serves as a registry and base class for
    resources, that is items that may be protected.

    To create a resource, subclass this class, add a foreign key named
    `resource_id` to resources.resource_id, and configure the class
    `__mapper_args__` dict with the polymorphic_identity key set to
    whatever value of discriminator you want. For example:

    class FileResource(Resource):
        __mapper_args__ = {'polymorphic_identity': 'file'}
        __tablename__ = 'files'

        resource_id = sa.Column(
            sa.Integer, sa.ForeignKey('resources.resource_id'), nullable=False)

        # your other attributes/methods

    For the example above, for each FileResource persisted, an accompanying
    Resource is persisted, with the resource_type set to 'file'.
    '''
    pass
