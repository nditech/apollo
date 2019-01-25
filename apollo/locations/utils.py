# -*- coding: utf-8 -*-
import networkx as nx

from apollo import services, utils
from apollo.core import db
from apollo.locations.models import LocationTypePath


def nuke_locations(location_set_id):
    # nuke locations
    services.locations.find(location_set_id=location_set_id).delete()
    db.session.commit()


def import_graph(graph, location_set, fresh_import=False):
    nodes = graph.get('nodes')
    edges = graph.get('edges')

    nx_graph = nx.DiGraph()

    for i, node in enumerate(nodes):
        # old implementation had ids as strings, current implementation
        # may be integers or integral strings
        if not utils.validate_uuid(str(node.get('id'))) and not fresh_import:
            # this is likely an existing division
            location_type = services.location_types.find(
                location_set=location_set,
                id=node.get('id')).first()

            if location_type:
                location_type.is_administrative = node.get(
                    'is_administrative')
                location_type.is_political = node.get('is_political')
                location_type.has_registered_voters = node.get(
                    'has_registered_voters')
                location_type.name_translations = node.get('nameTranslations')
                location_type.save()

        else:
            location_type = services.location_types.create(
                name_translations=node.get('nameTranslations'),
                is_administrative=node.get('is_administrative', False),
                is_political=node.get('is_political', False),
                has_registered_voters=node.get(
                    'has_registered_voters', False),
                location_set_id=location_set.id
            )

            # update the edges
            for edge in edges:
                if edge[0] == node.get('id'):
                    edge[0] = location_type.id
                if edge[1] == node.get('id'):
                    edge[1] = location_type.id

    # build graph for the closure table
    nx_graph.add_edges_from(edges)

    # build closure table
    path_lengths = dict(nx.all_pairs_shortest_path_length(nx_graph))

    for ancestor_id, paths in path_lengths.items():
        for descendant_id, depth in paths.items():
            path = LocationTypePath.query.filter_by(
                ancestor_id=ancestor_id,
                descendant_id=descendant_id,
                location_set_id=location_set.id
            ).first()

            # update the depth if we find an existing path
            if path:
                path.depth = depth
            else:
                path = LocationTypePath(
                    ancestor_id=ancestor_id, descendant_id=descendant_id,
                    depth=depth, location_set_id=location_set.id)

            db.session.add(path)
    db.session.commit()
