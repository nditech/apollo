# -*- coding: utf-8 -*-
from apollo.core import db
from apollo.dal.models import BaseModel


samples_locations = db.Table(
    'samples_locations',
    db.Column('sample_id', db.Integer, db.ForeignKey('sample.id'),
              primary_key=True),
    db.Column('location_id', db.Integer, db.ForeignKey('location.id'),
              primary_key=True))


class Sample(BaseModel):
    __tablename__ = 'sample'

    id = db.Column(
        db.Integer, db.Sequence('sample_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)

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
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)

    deployment = db.relationship('Deployment', backref='location_types')
    location_set = db.relationship('LocationSet', backref='location_types')

    def ancestors(self):
        return [p.ancestor_location_type for p in self.ancestor_paths]

    def descendants(self):
        return [p.descendant_location_type for p in self.descendant_paths]


class LocationTypePath(db.Model):
    __tablename__ = 'location_type_path'
    __table_args__ = (
        db.Index('location_type_paths_ancestor_idx', 'ancestor_id'),
        db.Index('location_type_paths_descendant_idx', 'descendant_id'))

    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)
    ancestor_id = db.Column(db.Integer, db.ForeignKey('location_type.id'),
                            primary_key=True)
    descendant_id = db.Column(db.Integer,
                              db.ForeignKey('location_type.id'),
                              primary_key=True)
    depth = db.Column(db.Integer)

    ancestor_location_type = db.relationship(
        'LocationType', backref='descendant_paths',
        primaryjoin=ancestor_id == LocationType.id)
    descendant_location_type = db.relationship(
        'LocationType', backref='ancestor_paths',
        primaryjoin=descendant_id == LocationType.id)


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
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)
    location_type_id = db.Column(
        db.Integer, db.ForeignKey('location_type.id'), nullable=False)

    deployment = db.relationship('Deployment', backref='locations')
    location_set = db.relationship('LocationSet', backref='locations')
    location_type = db.relationship('LocationType')
    samples = db.relationship(
        'Sample', backref='locations', secondary=samples_locations)

    def ancestors(self):
        return [p.ancestor_location for p in self.ancestor_paths]

    def descendants(self):
        return [p.descendant_location for p in self.descendant_paths]


class LocationPath(db.Model):
    __tablename__ = 'location_path'
    __table_args__ = (
        db.Index('location_paths_ancestor_idx', 'ancestor_id'),
        db.Index('location_paths_descendant_idx', 'descendant_id'))

    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)
    ancestor_id = db.Column(
        db.Integer, db.ForeignKey('location.id'), primary_key=True)
    descendant_id = db.Column(
        db.Integer, db.ForeignKey('location.id'), primary_key=True)
    depth = db.Column(db.Integer)

    ancestor_location = db.relationship(
        'Location', backref='descendant_paths',
        primaryjoin=ancestor_id == Location.id)
    descendant_location = db.relationship(
        'Location', backref='ancestor_paths',
        primaryjoin=descendant_id == Location.id)
