# -*- coding: utf-8 -*-
from uuid import uuid4

from sqlalchemy_utils import UUIDType

from apollo.core import db2


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
        db2.session.add(self)
        if commit:
            db2.session.commit()

        return self

    def delete(self, commit=True):
        db2.session.delete(self)
        return commit and db2.session.commit()


class BaseModel(CRUDMixin, db2.Model):
    '''Base model class'''
    __abstract__ = True

    uuid = db2.Column(UUIDType, default=uuid4)
