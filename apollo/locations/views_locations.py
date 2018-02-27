# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os

import networkx as nx

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, Response, url_for, abort)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_restful import Api
from flask_security import current_user, login_required
from apollo.helpers import load_source_file
from slugify import slugify_unicode
from sqlalchemy import not_

from apollo.frontend import permissions, route
from apollo import helpers, models, services, utils
from apollo.core import db, uploads
from apollo.locations import api, filters, tasks
from apollo.frontend.forms import (
    file_upload_form, generate_location_edit_form,
    generate_location_update_mapping_form, DummyForm)

bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
location_api = Api(bp)

admin_required = permissions.role('admin').require

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


@route(bp, '/location-sets', methods=['GET'])
@permissions.edit_locations.require(403)
@login_required
def location_set_list():
    args = request.args.to_dict(flat=False)
    page_title = _('Location sets')
    queryset = services.location_sets.find(deployment=g.deployment)
    template_name = 'frontend/location_set_list.html'

    page_spec = args.pop('page', [1])
    try:
        page = int(page_spec[0])
    except (IndexError, ValueError):
        page = 1

    context = {
        'location_sets': queryset.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE')),
        'page_title': page_title
    }

    return render_template(template_name, **context)


@route(bp, '/<int:location_set_id>/locations', methods=['GET'])
# @register_menu(
#     bp, 'user.locations_list', _('Locations'),
#     visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def location_list(location_set_id):
    template_name = 'frontend/location_list.html'
    page_title = _('Locations')

    queryset = services.locations.find(
        deployment=g.deployment, location_set_id=location_set_id)
    queryset_filter = filters.location_filterset(
        location_set_id=location_set_id)(queryset, request.args)

    args = request.args.to_dict(flat=False)
    args.update(location_set_id=location_set_id)
    page_spec = args.pop('page', None) or [1]
    page = int(page_spec[0])

    # NOTE: this was ordered by location type
    subset = queryset_filter.qs.order_by(models.Location.code)

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
            location_set_id=location_set_id,
            locations=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE')))

        return render_template(template_name, **ctx)


@route(bp, '/location/<int:id>', methods=['GET', 'POST'])
@permissions.edit_locations.require(403)
@login_required
def location_edit(id):
    template_name = 'frontend/location_edit.html'
    deployment = g.get('deployment')
    location = models.Location.query.filter_by(
        id=id, deployment=deployment).first_or_404()
    page_title = _('Edit Location')

    if request.method == 'GET':
        form = generate_location_edit_form(location)
    else:
        form = generate_location_edit_form(location, request.form)

        if form.validate():
            location.name = form.name.data
            location.save()

            return redirect(url_for(
                'locations.location_list',
                location_set_id=location.location_set_id))

    return render_template(template_name, form=form, page_title=page_title)


@route(bp, '/<int:location_set_id>/locations/import', methods=['POST'])
@permissions.import_locations.require(403)
@login_required
def locations_import(location_set_id):
    form = file_upload_form(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        filename = uploads.save(request.files['spreadsheet'])
        upload = models.UserUpload(
            deployment_id=g.deployment.id, upload_filename=filename,
            user_id=user.id)
        upload.save()

        return redirect(url_for('locations.location_headers',
                                location_set_id=location_set_id,
                                upload_id=upload.id))


@route(bp, '/<int:location_set_id>/locations/headers/<int:upload_id>',
       methods=['GET', 'POST'])
@permissions.import_locations.require(403)
@login_required
def location_headers(location_set_id, upload_id):
    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = services.user_uploads.fget_or_404(id=upload_id, user=user)
    filepath = uploads.path(upload.upload_filename)
    try:
        with open(filepath) as source_file:
            dataframe = load_source_file(source_file)
    except Exception:
        # delete loaded file
        os.remove(filepath)
        upload.delete()
        return abort(400)

    deployment = g.deployment
    location_set = services.location_sets.fget_or_404(id=location_set_id)
    headers = dataframe.columns
    template_name = 'frontend/location_headers.html'

    if request.method == 'GET':
        form = generate_location_update_mapping_form(
            deployment, headers, location_set)
        return render_template(template_name, form=form)
    else:
        form = generate_location_update_mapping_form(
            deployment, headers, location_set, request.form)

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
                'upload_id': upload.id,
                'mappings': data,
                'location_set_id': location_set_id
            }
            tasks.import_locations.apply_async(kwargs=kwargs)

            return redirect(url_for('locations.location_list',
                                    location_set_id=location_set_id))


@route(bp, '/<int:location_set_id>/locations/builder', methods=['GET', 'POST'])
# @register_menu(
#     bp, 'user.locations_builder', _('Administrative Divisions'),
#     visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def locations_builder(location_set_id):
    location_set = models.LocationSet.query.get_or_404(location_set_id)
    template_name = 'frontend/location_builder.html'
    page_title = _('Administrative Divisions')

    if request.method == 'POST' and request.form.get('divisions_graph'):
        nx_graph = nx.DiGraph()
        divisions_graph = json.loads(request.form.get('divisions_graph'))

        nodes = [cell for cell in divisions_graph.get('cells') if cell.get('type') == 'basic.Rect']
        links = [cell for cell in divisions_graph.get('cells') if cell.get('type') == 'link']

        valid_node_ids = [cell.get('id') for cell in nodes
                          if cell.get('id').isdigit()]

        # 1. Delete non-referenced location types
        unused_location_types = services.location_types.filter(
            models.LocationType.deployment == g.deployment,
            models.LocationType.location_set_id == location_set_id,
            not_(models.LocationType.id.in_(valid_node_ids))
        ).all()

        for unused_lt in unused_location_types:
            if len(unused_lt.locations) > 0:
                flash(_('Admin level %(name)s has locations assigned and cannot be deleted') % {'name': unused_lt.name},
                      category='locations_builder')
                continue
            unused_lt.delete()

        # 2. Create location types and update ids
        for i, node in enumerate(nodes):
            # TODO: remove this hack
            if not utils.validate_uuid(node.get('id')):
                lt = services.location_types.find(
                    deployment=g.deployment,
                    location_set=location_set,
                    id=node.get('id')).first()
            else:
                lt = None
            if lt:
                lt.is_administrative = node.get('is_administrative')
                lt.is_political = node.get('is_political')
                lt.name = node.get('label')
                lt.save()
            else:
                lt = services.location_types.create(
                    name=node.get('label'),
                    is_administrative=node.get('is_administrative'),
                    is_political=node.get('is_political'),
                    deployment_id=g.deployment.id,
                    location_set_id=location_set_id
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

        # 4. Build db relationships
        path_lengths = dict(nx.all_pairs_shortest_path_length(nx_graph))
        for link in links:
            if link['source'].get('id') and link['target'].get('id'):
                ancestors = nx.topological_sort(
                    nx_graph.subgraph(
                        nx.dfs_tree(
                            nx_graph.reverse(),
                            link['target'].get('id')).nodes()))

                for ancestor in ancestors:
                    path = models.LocationTypePath.query.filter_by(
                        ancestor_id=ancestor, descendant_id=link['target'].get(
                            'id'), location_set_id=location_set_id).first()
                    if not path:
                        path = models.LocationTypePath(
                            ancestor_id=ancestor,
                            descendant_id=link['target'].get('id'),
                            location_set_id=location_set_id,
                            depth=path_lengths[ancestor][link['target'].get(
                                'id')])
                        db.session.add(path)

        for node in nx_graph.nodes():
            path = models.LocationTypePath.query.filter_by(
                ancestor_id=node, descendant_id=node,
                location_set_id=location_set_id).first()
            if not path:
                path = models.LocationTypePath(
                    ancestor_id=node, descendant_id=node,
                    depth=0,
                    location_set_id=location_set_id)
                db.session.add(path)

        db.session.commit()

        # 5. convert graph to JSON
        divisions_graph['cells'] = nodes + links

        location_set.admin_divisions_graph = json.dumps(divisions_graph)
        location_set.save()

        flash(
            _('Your changes have been saved.'),
            category='locations_builder'
        )

    return render_template(template_name, page_title=page_title,
                           location_set=location_set)


@route(bp, '/<int:location_set_id>/locations/purge', methods=['POST'])
@admin_required(403)
@login_required
def nuke_locations(location_set_id):
    try:
        str_func = str
    except NameError:
        str_func = str

    flash(
        str_func(_('Locations, Checklists, Critical Incidents and Participants are being deleted.')),
        category='locations'
    )

    tasks.nuke_locations.apply_async(args=(location_set_id,))

    return redirect(url_for('locations.location_list',
                            location_set_id=location_set_id))
