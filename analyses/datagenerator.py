from django.core.cache import cache
import networkx as nx
import pandas as pd
from django_dag.models import Node, Edge
from core.models import *


def get_data_records(form, location_types=[], location_root=0):
    # fields that can store multiple variables are to be handled differently
    multivariate_fields = FormField.objects.filter(group__form=form, allow_multiple=True).values_list('tag', flat=True)
    regular_fields = FormField.objects.filter(group__form=form, allow_multiple=False).values_list('tag', flat=True)
    all_fields = list(multivariate_fields) + list(regular_fields)

    # retrieve normal and reversed locations graphs
    locations_graph = get_locations_graph()
    locations_graph_reversed = get_locations_graph(reverse=True)

    # if the location_root is defined, then we'll retrieve all sublocations based
    # on the location_root which will be used for retrieving submissions if not
    # we'll just use all locations in the graph
    if location_root:
        sub_location_ids = nx.dfs_tree(locations_graph_reversed, location_root).nodes()
    else:
        sub_location_ids = locations_graph.nodes()

    # in addition to retrieving field data, also retrieve the location_id
    submissions = list(Submission.objects.filter(location__pk__in=sub_location_ids, observer=None).data(all_fields).values(*(['location_id'] + all_fields)))

    for submission in submissions:
        '''
        Annotate the submissions with their ancestral location data as specified by `location_types`
        '''
        if location_types:
            ancestor_locations = get_location_ancestors_by_type(locations_graph, submission['location_id'], location_types)
            for ancestor_location in ancestor_locations:
                submission[ancestor_location['type']] = ancestor_location['name']

        # for numerical processing, we need to convert the responses into integers
        # note also that multivariates are converted into a list non numeric values
        # are represented as NaNs
        for _field in regular_fields:
            submission[_field] = int(submission[_field]) if submission[_field] else pd.np.nan
        for _field in multivariate_fields:
            submission[_field] = map(lambda x: int(x) if x else pd.np.nan, submission[_field].split(",") if submission[_field] else [])

    return pd.DataFrame(submissions)

def generate_process_data(location_root, form):
    pass

def generate_results_data(location_root, form):
    pass

def generate_locations_graph():
    '''
    Creates a directed acyclical graph of the locations database
    This is more performant for performing tree lookups and is 
    faster than the alternative of running several queries to
    retrieve this graph from the database
    '''
    nodes = Node.objects.filter(graph__name='location').values('pk', 'object_id')
    locations = Location.objects.filter(pk__in=[node['object_id'] for node in nodes]).values('pk', 'name', 'type__name')
    DG = nx.DiGraph()
    for location in locations:
        DG.add_node(location['pk'], name=location['name'], type=location['type__name'])
    edges = Edge.objects.filter(graph__name='location').values_list('node_from__object_id', 'node_to__object_id')
    for node_from, node_to in edges:
        DG.add_edge(node_from, node_to)
    return DG


def get_locations_graph(reverse=False):
    '''
    This provides a means of caching the generated
    graph and serving up the graph from the cache
    as needed.

    There's an optional parameter to retrieve the 
    reversed version of the graph
    '''
    graph = cache.get('reversed_locations_graph') if reverse else cache.get('locations_graph')
    if not graph:
        if reverse:
            graph = generate_locations_graph().reverse()
            cache.set('reversed_locations_graph', graph)
        else:
            graph = generate_locations_graph()
            cache.set('locations_graph', graph)
    return graph


def get_location_ancestors_by_type(graph, location_id, types=[]):
    '''
    This method provides a means of retrieving the ancestors of a particular location
    of specified types as defined in the LocationType model. It uses the depth-first-search
    algorithm in retrieving this subgraph
    '''
    nodes = graph.subgraph(nx.dfs_tree(graph, location_id).nodes()).nodes(data=True)
    return [node[1] for node in nodes if node[1]['type'] in types]
