# -*- coding: utf-8 -*-
from sqlalchemy import and_
from sqlalchemy.orm import aliased

from apollo.core import db
from apollo.dal.models import BaseModel


samples_locations = db.Table(
    'samples_locations',
    db.Column('sample_id', db.Integer, db.ForeignKey(
        'sample.id', ondelete='CASCADE'), primary_key=True),
    db.Column('location_id', db.Integer, db.ForeignKey(
        'location.id', ondelete='CASCADE'), primary_key=True))


class Sample(BaseModel):
    __tablename__ = 'sample'

    id = db.Column(
        db.Integer, db.Sequence('sample_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)

    deployment = db.relationship('Deployment', backref='samples')
    location_set = db.relationship('LocationSet', backref='samples')


class LocationType(BaseModel):
    __tablename__ = 'location_type'

    id = db.Column(
        db.Integer, db.Sequence('location_type_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    is_administrative = db.Column(db.Boolean, default=False)
    is_political = db.Column(db.Boolean, default=False)
    has_registered_voters = db.Column(db.Boolean, default=False)
    has_political_code = db.Column(db.Boolean, default=False)
    has_other_code = db.Column(db.Boolean, default=False)
    slug = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)

    deployment = db.relationship('Deployment', backref='location_types')
    location_set = db.relationship('LocationSet', backref='location_types')
    ancestor_paths = db.relationship(
        'LocationTypePath', order_by='desc(LocationTypePath.depth)',
        primaryjoin='LocationType.id == LocationTypePath.descendant_id',
        backref='descendant_location_type')
    descendant_paths = db.relationship(
        'LocationTypePath', order_by='LocationTypePath.depth',
        primaryjoin='LocationType.id == LocationTypePath.ancestor_id',
        backref='ancestor_location_type')

    def __str__(self):
        return self.name or ''

    def ancestors(self):
        return [
            p.ancestor_location_type for p in self.ancestor_paths
            if p.depth != 0
        ]

    def descendants(self):
        return [
            p.descendant_location_type for p in self.descendant_paths
            if p.depth != 0
        ]

    @classmethod
    def root(cls, location_set_id):
        anc = aliased(LocationTypePath)
        q = LocationTypePath.query.with_entities(
            LocationTypePath.descendant_id).filter_by(
                depth=0,
                location_set_id=location_set_id
            ).outerjoin(
                anc,
                and_(
                    anc.descendant_id == LocationTypePath.descendant_id,
                    anc.ancestor_id != LocationTypePath.ancestor_id)
            ).filter(anc.ancestor_id == None)   # noqa

        return cls.query.filter(
            cls.id.in_(q), cls.location_set_id == location_set_id).first()


class LocationTypePath(db.Model):
    __tablename__ = 'location_type_path'
    __table_args__ = (
        db.Index('location_type_paths_ancestor_idx', 'ancestor_id'),
        db.Index('location_type_paths_descendant_idx', 'descendant_id'))

    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)
    ancestor_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), primary_key=True)
    descendant_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), primary_key=True)
    depth = db.Column(db.Integer)


class Location(BaseModel):
    __tablename__ = 'location'
    __table_args__ = (
        db.UniqueConstraint('location_set_id', 'code'),)

    id = db.Column(
        db.Integer, db.Sequence('location_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    code = db.Column(db.String, index=True, nullable=False)
    political_code = db.Column(db.String)
    other_code = db.Column(db.String)
    registered_voters = db.Column(db.Integer, default=0)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    location_set_id = db.Column(db.Integer, db.ForeignKey(
        'location_set.id', ondelete='CASCADE'), nullable=False)
    location_type_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), nullable=False)

    deployment = db.relationship('Deployment', backref='locations')
    location_set = db.relationship('LocationSet', backref='locations')
    location_type = db.relationship('LocationType', backref='locations')
    samples = db.relationship(
        'Sample', backref='locations', secondary=samples_locations)

    ancestor_paths = db.relationship(
        'LocationPath', order_by='desc(LocationPath.depth)',
        primaryjoin='Location.id == LocationPath.descendant_id',
        backref='descendant_location')
    descendant_paths = db.relationship(
        'LocationPath', order_by='LocationPath.depth',
        primaryjoin='Location.id == LocationPath.ancestor_id',
        backref='ancestor_location')

    def ancestors(self):
        return [
            p.ancestor_location for p in self.ancestor_paths
            if p.depth != 0
        ]

    def descendants(self):
        return [
            p.descendant_location for p in self.descendant_paths
            if p.depth != 0
        ]

    @classmethod
    def root(cls, location_set_id):
        anc = aliased(LocationPath)
        q = LocationPath.query.with_entities(
            LocationPath.descendant_id).filter_by(
                depth=0,
                location_set_id=location_set_id
            ).outerjoin(
                anc,
                and_(
                    anc.descendant_id == LocationPath.descendant_id,
                    anc.ancestor_id != LocationPath.ancestor_id)
            ).filter(anc.ancestor_id == None)   # noqa

        return cls.query.filter(
            cls.id.in_(q), cls.location_set_id == location_set_id).first()


class LocationPath(db.Model):
    __tablename__ = 'location_path'
    __table_args__ = (
        db.Index('location_paths_ancestor_idx', 'ancestor_id'),
        db.Index('location_paths_descendant_idx', 'descendant_id'))

    location_set_id = db.Column(db.Integer, db.ForeignKey(
        'location_set.id', ondelete='CASCADE'), nullable=False)
    ancestor_id = db.Column(db.Integer, db.ForeignKey(
        'location.id', ondelete='CASCADE'), primary_key=True)
    descendant_id = db.Column(db.Integer, db.ForeignKey(
        'location.id', ondelete='CASCADE'), primary_key=True)
    depth = db.Column(db.Integer)
