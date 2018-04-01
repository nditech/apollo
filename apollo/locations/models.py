# -*- coding: utf-8 -*-
import networkx as nx
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import aliased

from apollo.core import db
from apollo.dal.models import BaseModel


class LocationSet(BaseModel):
    __tablename__ = 'location_set'

    id = db.Column(
        db.Integer, db.Sequence('location_set_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    deployment = db.relationship('Deployment', backref='location_sets')

    def __str__(self):
        return self.name or ''

    def make_admin_divisions_graph(self):
        edges = LocationTypePath.query.filter(
            LocationTypePath.location_set_id == self.id,
            LocationTypePath.depth > 0
        ).with_entities(
            LocationTypePath.ancestor_id,
            LocationTypePath.descendant_id
        ).all()

        nodes = LocationType.query.filter(
            LocationType.location_set_id == self.id
        ).with_entities(
            LocationType.id,
            LocationType.name,
            LocationType.has_other_code,
            LocationType.has_political_code,
            LocationType.has_registered_voters
        ).all()

        nx_graph = nx.DiGraph()
        nx_graph.add_edges_from(edges)

        graph = {
            'nodes': [n._asdict() for n in nodes],
            'edges': list(nx.dfs_edges(nx_graph))
        }

        return graph


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
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)

    location_set = db.relationship('LocationSet', backref=db.backref(
        'samples', lazy='dynamic'))


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
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)

    location_set = db.relationship('LocationSet', backref=db.backref(
        'location_types', lazy='dynamic'))
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

    def children(self):
        return [
            p.descendant_location_type for p in self.descendant_paths
            if p.depth == 1
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
    location_set_id = db.Column(db.Integer, db.ForeignKey(
        'location_set.id', ondelete='CASCADE'), nullable=False)
    location_type_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    extra_data = db.Column(JSONB)

    location_set = db.relationship('LocationSet', backref=db.backref(
        'locations', lazy='dynamic'))
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

    def children(self):
        return [
            p.descendant_location for p in self.descendant_paths
            if p.depth == 1
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

    def make_path(self):
        self._cached_path = getattr(self, '_cached_path', None)
        if not self._cached_path:
            data = {ans.location_type.name: ans.name for ans in self.ancestors()}
            data.update({self.location_type.name: self.name})

            self._cached_path = data

        return self._cached_path

    def __repr__(self):
        return self.name


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


class LocationDataField(db.Model):
    __tablename__ = 'location_data_field'

    id = db.Column(
        db.Integer, db.Sequence('location_data_field_id_seq'),
        primary_key=True)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    label = db.Column(db.String, nullable=False)
    visible_in_lists = db.Column(db.Boolean, default=False)
    location_set = db.relationship('LocationSet', backref='extra_fields')
