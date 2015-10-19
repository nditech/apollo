# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
from datetime import datetime

import networkx as nx

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, Response, url_for, abort)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.restful import Api
from flask.ext.security import current_user, login_required
from apollo.helpers import load_source_file, stash_file
from mongoengine import ValidationError
from slugify import slugify_unicode

from apollo.frontend import filters, permissions, route
from apollo import helpers, models, services
from apollo.locations import api
from apollo.locations.tasks import import_locations
from apollo.frontend.forms import (
    file_upload_form, generate_location_edit_form,
    generate_location_update_mapping_form, DummyForm)

bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
location_api = Api(bp)


location_api.add_resource(
    api.LocationTypeItemResource,
    '/api/locationtype/<loc_type_id>',
    endpoint='api.locationtype'
)
location_api.add_resource(
    api.LocationTypeListResource,
    '/api/locationtypes/',
    endpoint='api.locationtypes'
)
location_api.add_resource(
    api.LocationItemResource,
    '/api/location/<location_id>',
    endpoint='api.location'
)
location_api.add_resource(
    api.LocationListResource,
    '/api/locations/',
    endpoint='api.locations'
)


@route(bp, '/locations/', methods=['GET'])
@register_menu(
    bp, 'user.locations_list', _('Locations'),
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

    if request.args.get('export') and permissions.export_locations.can():
        # Export requested
        dataset = services.locations.export_list(queryset_filter.qs)
        basename = slugify_unicode('%s locations %s' % (
            g.event.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        ctx = dict(
            args=args,
            filter_form=queryset_filter.form,
            page_title=page_title,
            form=DummyForm(),
            locations=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE')))

        return render_template(template_name, **ctx)


@route(bp, '/location/<pk>', methods=['GET', 'POST'])
@permissions.edit_locations.require(403)
@login_required
def location_edit(pk):
    template_name = 'frontend/location_edit.html'
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


@route(bp, '/locations/import', methods=['POST'])
@permissions.import_locations.require(403)
@login_required
def locations_import():
    form = file_upload_form(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        event = services.events.get_or_404(pk=form.event.data)
        upload = stash_file(request.files['spreadsheet'], user, event)
        upload.save()

        return redirect(url_for(
            'locations.location_headers',
            pk=unicode(upload.id)
        ))


@route(bp, '/locations/headers/<pk>', methods=['GET', 'POST'])
@permissions.import_locations.require(403)
@login_required
def location_headers(pk):
    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = services.user_uploads.get_or_404(pk=pk, user=user)
    try:
        dataframe = load_source_file(upload.data)
    except Exception:
        # delete loaded file
        upload.data.delete()
        upload.delete()
        return abort(400)

    deployment = g.deployment
    headers = dataframe.columns
    template_name = 'frontend/location_headers.html'

    if request.method == 'GET':
        form = generate_location_update_mapping_form(deployment, headers)
        return render_template(template_name, form=form)
    else:
        form = generate_location_update_mapping_form(
            deployment, headers, request.form)

        if not form.validate():
            return render_template(
                template_name,
                form=form
            )
        else:
            # get header mappings
            data = form.data.copy()

            # invoke task asynchronously
            kwargs = {
                'upload_id': unicode(upload.id),
                'mappings': data
            }
            import_locations.apply_async(kwargs=kwargs)

            return redirect(url_for('locations.locations_list'))


@route(bp, '/locations/builder', methods=['GET', 'POST'])
@register_menu(
    bp, 'user.locations_builder', _('Administrative Divisions'),
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

        # 5. Update ancestor count
        for location_type in services.location_types.find():
            location_type.save()

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
