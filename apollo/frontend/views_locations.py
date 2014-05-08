# -*- coding: utf-8 -*-
from __future__ import absolute_import
from flask import (
    Blueprint, g, redirect, render_template, request, url_for, flash,
    current_app
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.restful import Api
from flask.ext.security import login_required
from flask.ext.menu import register_menu
from mongoengine import ValidationError
from .. import models, services, helpers
from ..locations.api import LocationTypeItemResource, LocationTypeListResource
from . import route, permissions, filters
from .forms import generate_location_edit_form
import json
import networkx as nx

bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
location_api = Api(bp)

location_api.add_resource(
    LocationTypeItemResource,
    '/api/locationtypes/<loc_type_id>',
    endpoint='api.locationtype'
)
location_api.add_resource(
    LocationTypeListResource,
    '/api/locationtypes',
    endpoint='api.locationtypes'
)


@route(bp, '/locations/', methods=['GET'])
@register_menu(
    bp, 'locations_list', _('Locations'),
    visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def locations_list():
    template_name = 'frontend/location_list.html'
    page_title = _('Locations')

    queryset = services.locations.find()
    queryset_filter = filters.location_filterset()(queryset, request.args)

    args = request.args.copy()
    page = int(args.pop('page', '1'))

    subset = queryset_filter.qs.order_by('location_type')

    ctx = dict(
        args=args,
        filter_form=queryset_filter.form,
        page_title=page_title,
        locations=subset.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE')))

    return render_template(template_name, **ctx)


@route(bp, '/location/<pk>', methods=['GET', 'POST'])
@register_menu(
    bp, 'location_edit', _('Edit Location'),
    visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def location_edit(pk):
    template_name = 'core/location_edit.html'
    deployment = g.get('deployment')
    location = models.Location.objects.get_or_404(pk=pk, deployment=deployment)
    page_title = _('Edit Location')

    if request.method == 'GET':
        form = generate_location_edit_form(location)
    else:
        form = generate_location_edit_form(location, request.form)

        if form.validate():
            form.populate_obj(location)
            location.save()

            return redirect(url_for('core.location_list'))

    return render_template(template_name, form=form, page_title=page_title)


@route(bp, '/locations/import', methods=['GET', 'POST'])
@register_menu(
    bp, 'locations_import', _('Import Locations'),
    visible_when=lambda: permissions.import_locations.can())
@permissions.import_locations.require(403)
@login_required
def locations_import():
    return ''


@route(bp, '/locations/builder', methods=['GET', 'POST'])
@register_menu(
    bp, 'locations_builder', _('Administrative Divisions'),
    visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def locations_builder():
    template_name = 'frontend/location_builder.html'
    page_title = _('Administrative Divisions')

    if request.method == 'POST' and request.form.get('divisions_graph'):
        nx_graph = nx.DiGraph()
        divisions_graph = json.loads(request.form.get('divisions_graph'))

        nodes = filter(
            lambda cell: cell.get('type') == 'basic.Rect',
            divisions_graph.get('cells'))
        links = filter(
            lambda cell: cell.get('type') == 'link',
            divisions_graph.get('cells'))

        valid_node_ids = map(
            lambda cell: cell.get('id'),
            filter(
                lambda cell: helpers.is_objectid(cell.get('id')),
                nodes))

        # 1. Delete non-referenced location types
        services.location_types.find(id__nin=valid_node_ids).delete()

        # 2. Create location types and update ids
        for i, node in enumerate(nodes):
            try:
                lt = services.location_types.find().get(id=node.get('id'))
                lt.is_administrative = node.get('is_administrative')
                lt.is_political = node.get('is_political')
                lt.name = node.get('label')
                lt.ancestors_ref = []
                lt.save()
            except (models.LocationType.DoesNotExist, ValidationError):
                lt = services.location_types.create(
                    name=node.get('label'),
                    is_administrative=node.get('is_administrative'),
                    is_political=node.get('is_political')
                    )

                # update graph node and link ids
                for j, link in enumerate(links):
                    if link['source'].get('id', None) == node.get('id'):
                        links[j]['source']['id'] = str(lt.id)
                    if link['target'].get('id', None) == node.get('id'):
                        links[j]['target']['id'] = str(lt.id)

            nodes[i]['id'] = str(lt.id)

        # 3. Build graph
        for node in nodes:
            nx_graph.add_node(node.get('id'))
        for link in links:
            if link['source'].get('id') and link['target'].get('id'):
                nx_graph.add_edge(
                    link['source'].get('id'),
                    link['target'].get('id'))

        # 4. Update ancestor relationships
        for link in links:
            if link['source'].get('id') and link['target'].get('id'):
                ancestors = nx.topological_sort(
                    nx_graph.reverse(),
                    nx_graph.reverse().subgraph(
                        nx.dfs_tree(
                            nx_graph.reverse(),
                            link['target'].get('id')).nodes()).nodes())
                services.location_types.find().get(
                    id=link['target'].get('id')).update(
                    add_to_set__ancestors_ref=filter(
                        lambda ancestor: ancestor != link['target'].get('id'),
                        ancestors))

        divisions_graph['cells'] = nodes + links

        g.deployment.administrative_divisions_graph = json.dumps(
            divisions_graph)
        g.deployment.save()
        g.deployment.reload()

        flash(
            _('Your changes have been saved.'),
            category='locations_builder'
        )

    return render_template(template_name, page_title=page_title)
