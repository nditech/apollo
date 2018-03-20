# -*- coding: utf-8 -*-
'''Base model classes.

The concept of resources and the permissions implementation
is liberally adapted (aka stolen) from the source of ziggurat_foundations
(https://github.com/ergo/ziggurat-foundations)
'''

from sqlalchemy.ext.declarative import declared_attr

from apollo.core import db


class CRUDMixin(object):
    '''CRUD mixin class'''

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

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

    id = db.Column(
        db.Integer, db.Sequence('permission_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    deployment = db.relationship('Deployment', backref='permissions')

    def __str__(self):
        return self.description if self.description else self.name


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
