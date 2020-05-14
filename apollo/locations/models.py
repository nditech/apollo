# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext as _
from geoalchemy2 import Geometry
import networkx as nx
from sqlalchemy import and_, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import aliased

from apollo.core import db
from apollo.dal.models import BaseModel, Resource, translation_hybrid


class LocationSet(BaseModel):
    __tablename__ = 'location_set'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('location_sets', cascade='all, delete',
                           passive_deletes=True))
    is_finalized = db.Column(db.Boolean, default=False)

    def __str__(self):
        return self.name or ''

    def make_admin_divisions_graph(self):
        edges = LocationTypePath.query.filter(
            LocationTypePath.location_set_id == self.id,
            LocationTypePath.depth == 1
        ).with_entities(
            LocationTypePath.ancestor_id,
            LocationTypePath.descendant_id
        ).all()

        di_graph = nx.DiGraph()
        di_graph.add_edges_from(edges)
        sorted_nodes = list(nx.topological_sort(di_graph))
        sorted_edges = list(di_graph.edges(sorted_nodes))

        location_types = [LocationType.query.filter(
            LocationType.location_set_id == self.id,
            LocationType.id == _id).one() for _id in sorted_nodes]

        nodes = [{
            'id': lt.id,
            'name': lt.name,
            'nameTranslations': {
                locale: tr
                for locale, tr in lt.name_translations.items()
            } if lt.name_translations else {},
            'has_registered_voters': lt.has_registered_voters,
            'has_coordinates': lt.has_coordinates,
            'is_administrative': lt.is_administrative,
            'is_political': lt.is_political,
        } for lt in location_types]

        graph = {
            'nodes': nodes,
            'edges': sorted_edges
        }

        return graph

    def get_import_fields(self):
        fields = {}

        extra_fields = LocationDataField.query.filter_by(
            location_set_id=self.id).all()
        location_types = LocationTypePath.query.filter_by(
            location_set=self
        ).join(
            LocationType, LocationType.id == LocationTypePath.ancestor_id
        ).with_entities(
            LocationType
        ).group_by(
            LocationTypePath.ancestor_id,
            LocationType.id
        ).order_by(
            func.count(LocationTypePath.ancestor_id).desc(),
            LocationType.name
        ).all()

        for lt in location_types:
            lt_data = {}

            for locale, language in self.deployment.languages.items():
                lt_data[f'{lt.id}_name_{locale}'] = _(
                    '%(location_type)s Name (%(language)s)',
                    location_type=lt.name, language=language)

            lt_data['{}_code'.format(lt.id)] = _('%(location_type)s Code',
                                                 location_type=lt.name)
            if lt.has_coordinates:
                lt_data['{}_lat'.format(lt.id)] = _(
                    '%(location_type)s Latitude', location_type=lt.name)
                lt_data['{}_lon'.format(lt.id)] = _(
                    '%(location_type)s Longitude', location_type=lt.name)

            for ex_field in extra_fields:
                lt_data['{}:{}'.format(lt.id, ex_field.id)] = _(
                    '%(location_type)s %(field_label)s',
                    location_type=lt.name,
                    field_label=ex_field.label)

            if lt.has_registered_voters:
                lt_data['{}_rv'.format(lt.id)] =  \
                    _('%(location_type)s registered voters',
                      location_type=lt.name)
            fields.update(lt_data)

        return fields

    @property
    def events(self):
        return {
            event
            for participant_set in self.participant_sets
            for event in participant_set.events
        }


class LocationType(BaseModel):
    __tablename__ = 'location_type'

    id = db.Column(db.Integer, primary_key=True)
    name_translations = db.Column(JSONB)
    is_administrative = db.Column(db.Boolean, default=False)
    is_political = db.Column(db.Boolean, default=False)
    has_registered_voters = db.Column(db.Boolean, default=False)
    slug = db.Column(db.String)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)
    has_coordinates = db.Column(
        db.Boolean, default=False, server_default=false())

    name = translation_hybrid(name_translations)

    location_set = db.relationship('LocationSet', backref=db.backref(
        'location_types', cascade='all, delete', lazy='dynamic',
        passive_deletes=True))
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
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)
    ancestor_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), primary_key=True)
    descendant_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), primary_key=True)
    depth = db.Column(db.Integer)

    location_set = db.relationship(
        'LocationSet', backref=db.backref(
            'location_type_paths', cascade='all, delete',
            passive_deletes=True))


class Location(BaseModel):
    __tablename__ = 'location'
    __table_args__ = (
        db.UniqueConstraint('location_set_id', 'code'),)

    id = db.Column(db.Integer, primary_key=True)
    name_translations = db.Column(JSONB)
    code = db.Column(db.String, index=True, nullable=False)
    registered_voters = db.Column(db.Integer, default=0)
    location_set_id = db.Column(db.Integer, db.ForeignKey(
        'location_set.id', ondelete='CASCADE'), nullable=False)
    location_type_id = db.Column(db.Integer, db.ForeignKey(
        'location_type.id', ondelete='CASCADE'), nullable=False)
    geom = db.Column(Geometry('POINT', srid=4326))
    extra_data = db.Column(JSONB)

    name = translation_hybrid(name_translations)

    location_set = db.relationship('LocationSet', backref=db.backref(
        'locations', cascade='all, delete', lazy='dynamic'))
    location_type = db.relationship(
        'LocationType',
        backref=db.backref('locations', cascade='all, delete',
                           passive_deletes=True))

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

    def parents(self):
        return [
            p.ancestor_location for p in self.ancestor_paths
            if p.depth == 1
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
            data = {
                ans.location_type.name: ans.name for ans in self.ancestors()}
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

    location_set = db.relationship(
        'LocationSet',
        backref=db.backref('location_paths', cascade='all, delete',
                           passive_deletes=True))


class LocationDataField(Resource):
    __mapper_args__ = {'polymorphic_identity': 'location_data_field'}
    __tablename__ = 'location_data_field'

    id = db.Column(db.Integer, primary_key=True)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)
    name = db.Column(db.String, nullable=False)
    label = db.Column(db.String, nullable=False)
    visible_in_lists = db.Column(db.Boolean, default=False)
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'))
    location_set = db.relationship(
        'LocationSet',
        backref=db.backref('extra_fields', cascade='all, delete',
                           passive_deletes=True))

    def __str__(self):
        return gettext('LocationDataField - %(name)s in %(location_set)s',
                       name=self.name, location_set=self.location_set.name)


LocationTranslations = func.jsonb_each_text(
    Location.name_translations).alias('translations')
LocationTypeTranslations = func.jsonb_each_text(
    LocationType.name_translations).alias('translations')
