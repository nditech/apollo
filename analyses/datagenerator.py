from django.core.cache import cache
import networkx as nx
from django_dag.models import Node, Edge
from core.models import Location


def generate_locations_graph():
    nodes = Node.objects.filter(graph__name='location').values('pk', 'object_id')
    locations = Location.objects.filter(pk__in=[node['object_id'] for node in nodes]).values('pk', 'name', 'type__name')
    DG = nx.DiGraph()
    for location in locations:
        DG.add_node(location['pk'], name=location['name'], type=location['type__name'])
    edges = Edge.objects.filter(graph__name='location').values_list('node_from__object_id', 'node_to__object_id')
    for node_from, node_to in edges:
        DG.add_edge(node_from, node_to)
    return DG


def get_locations_graph():
    graph = cache.get('locations_graph')
    if not graph:
        graph = generate_locations_graph()
        cache.set('locations_graph', graph)
    return graph


def get_location_ancestors_by_type(graph, location_id, types=['Province']):
    nodes = graph.subgraph(nx.dfs_tree(graph, location_id).nodes()).nodes(data=True)
    return [node[1] for node in nodes if node[1]['type'] in types]
