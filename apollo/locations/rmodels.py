# -*- coding: utf-8 -*-
from apollo.core import db2
from apollo.dal.models import BaseModel


samples_locations = db2.Table(
    'samples_locations',
    db2.Column('sample_id', db2.Integer, db2.ForeignKey('sample.id'),
               primary_key=True),
    db2.Column('location_id', db2.Integer, db2.ForeignKey('location.id'),
               primary_key=True))


class Sample(BaseModel):
    __tablename__ = 'sample'

    id = db2.Column(
        db2.Integer, db2.Sequence('sample_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    location_set_id = db2.Column(
        db2.Integer, db2.ForeignKey('location_set.id'))

    deployment = db2.relationship('Deployment', backref='samples')
    location_set = db2.relationship('LocationSet', backref='samples')


class LocationType(BaseModel):
    __tablename__ = 'location_type'

    id = db2.Column(
        db2.Integer, db2.Sequence('location_type_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    is_administrative = db2.Column(db2.Boolean, default=False)
    is_political = db2.Column(db2.Boolean, default=False)
    has_registered_voters = db2.Column(db2.Boolean, default=False)
    has_political_code = db2.Column(db2.Boolean, default=False)
    has_other_code = db2.Column(db2.Boolean, default=False)
    slug = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    location_set_id = db2.Column(
        db2.Integer, db2.ForeignKey('location_set.id'))

    deployment = db2.relationship('Deployment', backref='location_types')
    location_set = db2.relationship('LocationSet', backref='location_types')

    def ancestors(self):
        return [p.ancestor_location_type for p in self.ancestor_paths]

    def descendants(self):
        return [p.descendant_location_type for p in self.descendant_paths]


class LocationTypePath(db2.Model):
    __tablename__ = 'location_type_path'
    __table_args__ = (
        db2.Index('location_type_paths_ancestor_idx', 'ancestor_id'),
        db2.Index('location_type_paths_descendant_idx', 'descendant_id'))

    ancestor_id = db2.Column(db2.Integer, db2.ForeignKey('location_type.id'),
                             primary_key=True)
    descendant_id = db2.Column(db2.Integer,
                               db2.ForeignKey('location_type.id'),
                               primary_key=True)
    depth = db2.Column(db2.Integer)

    ancestor_location_type = db2.relationship(
        'LocationType', backref='descendant_paths',
        primaryjoin=ancestor_id == LocationType.id)
    descendant_location_type = db2.relationship(
        'LocationType', backref='ancestor_paths',
        primaryjoin=descendant_id == LocationType.id)


class Location(BaseModel):
    __tablename__ = 'location'

    id = db2.Column(
        db2.Integer, db2.Sequence('location_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    code = db2.Column(db2.String)
    political_code = db2.Column(db2.String)
    other_code = db2.Column(db2.String)
    registered_voters = db2.Column(db2.Integer, default=0)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    location_set_id = db2.Column(
        db2.Integer, db2.ForeignKey('location_set.id'))
    location_type_id = db2.Column(
        db2.Integer, db2.ForeignKey('location_type.id'))

    deployment = db2.relationship('Deployment', backref='locations')
    location_set = db2.relationship('LocationSet', backref='locations')
    location_type = db2.relationship('LocationType')
    samples = db2.relationship(
        'Sample', backref='locations', secondary=samples_locations)

    def ancestors(self):
        return [p.ancestor_location for p in self.ancestor_paths]

    def descendants(self):
        return [p.descendant_location for p in self.descendant_paths]


class LocationPath(db2.Model):
    __tablename__ = 'location_path'
    __table_args__ = (
        db2.Index('location_paths_ancestor_idx', 'ancestor_id'),
        db2.Index('location_paths_descendant_idx', 'descendant_id'))

    ancestor_id = db2.Column(
        db2.Integer, db2.ForeignKey('location.id'), primary_key=True)
    descendant_id = db2.Column(
        db2.Integer, db2.ForeignKey('location.id'), primary_key=True)
    depth = db2.Column(db2.Integer)

    ancestor_location = db2.relationship(
        'Location', backref='descendant_paths',
        primaryjoin=ancestor_id == Location.id)
    descendant_location = db2.relationship(
        'Location', backref='ancestor_paths',
        primaryjoin=descendant_id == Location.id)
