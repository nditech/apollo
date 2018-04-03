# -*- coding: utf-8 -*-
from datetime import datetime
from io import BytesIO
import json
import os

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, Response, url_for, abort, stream_with_context,
                   send_file)
from flask_babelex import lazy_gettext as _
from flask_restful import Api
from flask_security import current_user, login_required
from slugify import slugify_unicode
from sqlalchemy import not_, or_

from apollo import models, services
from apollo.core import db, uploads
from apollo.frontend import permissions, route
from apollo.frontend.forms import (
    file_upload_form, generate_location_edit_form,
    generate_location_update_mapping_form, DummyForm)
from apollo.helpers import load_source_file
from apollo.locations import api, filters, forms, tasks
from apollo.locations.utils import import_graph


bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
location_api = Api(bp)

admin_required = permissions.role('admin').require

location_api.add_resource(
    api.LocationTypeItemResource,
    '/api/locationtype/<int:loc_type_id>',
    endpoint='api.locationtype'
)
location_api.add_resource(
    api.LocationTypeListResource,
    '/api/locationtypes/',
    endpoint='api.locationtypes'
)
location_api.add_resource(
    api.LocationItemResource,
    '/api/location/<int:location_id>',
    endpoint='api.location'
)
location_api.add_resource(
    api.LocationListResource,
    '/api/locations/',
    endpoint='api.locations'
)


@route(bp, '/locations/set/<int:location_set_id>', methods=['GET'])
@permissions.edit_locations.require(403)
@login_required
def location_list(location_set_id):
    template_name = 'frontend/location_list.html'
    page_title = _('Locations')

    queryset = services.locations.find(location_set_id=location_set_id)
    queryset_filter = filters.location_filterset(
        location_set_id=location_set_id)(queryset, request.args)
    extra_fields = [
        field for field in models.LocationDataField.query.filter_by(
            location_set_id=location_set_id) if field.visible_in_lists]

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
            stream_with_context(dataset),
            headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        ctx = dict(
            args=args,
            extra_fields=extra_fields,
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
    location = models.Location.query.filter_by(id=id).first_or_404()
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


@route(bp, '/locations/set/<int:location_set_id>/import', methods=['POST'])
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


@route(bp, '/locations/set/<int:location_set_id>'
           '/headers/upload/<int:upload_id>',
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

    location_set = services.location_sets.fget_or_404(id=location_set_id)
    headers = dataframe.columns
    template_name = 'frontend/location_headers.html'

    if request.method == 'GET':
        form = generate_location_update_mapping_form(headers, location_set)
        return render_template(template_name, form=form)
    else:
        form = generate_location_update_mapping_form(
            headers, location_set, request.form)

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


@route(bp, '/locations/set/<int:location_set_id>/builder',
       methods=['GET', 'POST'])
# @register_menu(
#     bp, 'user.locations_builder', _('Administrative Divisions'),
#     visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def locations_builder(location_set_id):
    location_set = models.LocationSet.query.get_or_404(location_set_id)

    has_admin_divisions = db.session.query(services.location_types.find(
        location_set_id=location_set_id).exists()).scalar()

    template_name = 'frontend/location_builder.html'
    page_title = _('Administrative Divisions')
    form = forms.AdminDivisionImportForm()

    if request.method == 'POST' and request.form.get('divisions_graph'):
        divisions_graph = json.loads(request.form.get('divisions_graph'))
        nodes = divisions_graph.get('nodes')

        # find any divisions that were not included in the saved graph
        # and delete them if there are no linked locations
        saved_node_ids = [node.get('id') for node in nodes
                          if str(node.get('id')).isdigit()]
        unused_location_types = services.location_types.filter(
            models.LocationType.location_set_id == location_set_id,
            not_(models.LocationType.id.in_(saved_node_ids))
        ).all()

        for unused_lt in unused_location_types:
            query = services.locations.find(location_type=unused_lt)
            if db.session.query(query.exists()).scalar():
                flash(_('Admin level %(name)s has locations assigned '
                        'and cannot be deleted', name=unused_lt.name),
                      category='locations_builder')
                continue

            # explicitly doing this because we didn't add a cascade
            # to the backref
            models.LocationTypePath.query.filter(or_(
                models.LocationTypePath.ancestor_id == unused_lt.id,
                models.LocationTypePath.descendant_id == unused_lt.id
            )).delete()
            unused_lt.delete()

        import_graph(divisions_graph, location_set)

        flash(
            _('Your changes have been saved.'),
            category='locations_builder'
        )

    return render_template(template_name, page_title=page_title,
                           location_set=location_set, form=form,
                           has_admin_divisions=has_admin_divisions)


@route(bp, '/locations/set/<int:location_set_id>/purge', methods=['POST'])
@admin_required(403)
@login_required
def nuke_locations(location_set_id):
    flash(
        str(_('Locations, Checklists, Critical Incidents and '
            'Participants are being deleted.')),
        category='locations'
    )

    tasks.nuke_locations.apply_async(args=(location_set_id,))

    return redirect(url_for('locations.location_list',
                            location_set_id=location_set_id))


@route(bp, '/samples/<int:location_set_id>/new', methods=['GET', 'POST'])
@permissions.edit_locations.require(403)
@login_required
def sample_new(location_set_id):
    page_title = _('Create new sample')
    sample_form = forms.SampleForm(data={'location_data': json.dumps([])})
    template_name = 'frontend/sample_edit.html'

    context = {
        'form': sample_form,
        'location_set_id': location_set_id,
        'page_title': page_title
    }

    if not sample_form.validate_on_submit():
        return render_template(template_name, **context)

    sample = services.samples.create(
        location_set_id=location_set_id, name=sample_form.name.data)

    location_data = json.loads(sample_form.location_data.data)
    if location_data:
        codes = [i[0].strip() for i in location_data if i[0]]
        sample.locations = services.locations.filter(
            models.Location.code.in_(codes),
            models.Location.location_set_id == sample.location_set_id
        ).all()
        sample.save()

    return redirect(url_for('.sample_list', location_set_id=location_set_id))


@route(bp, '/samples/set/<int:location_set_id>', methods=['GET'])
@permissions.edit_locations.require(403)
@login_required
def sample_list(location_set_id):
    page_title = _('Samples')
    samples = services.samples.find(location_set_id=location_set_id)
    template_name = 'frontend/sample_list.html'

    args = request.args.to_dict(flat=False)
    page_spec = args.pop('page', None) or [1]
    page = int(page_spec[0])

    context = {
        'location_set_id': location_set_id,
        'page_title': page_title,
        'samples': samples.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE'))
    }

    return render_template(template_name, **context)


@route(bp, '/sample/<int:sample_id>', methods=['GET', 'POST'])
@permissions.edit_locations.require(403)
@login_required
def sample_edit(sample_id):
    sample = services.samples.fget_or_404(id=sample_id)
    page_title = _('Edit sample %(name)s', name=sample.name)
    template_name = 'frontend/sample_edit.html'

    if request.method == 'GET':
        location_data = [{
            'code': l.code,
            'name': l.name
        } for l in sample.locations]

        sample_form = forms.SampleForm(data={
            'name': sample.name,
            'location_data': json.dumps(location_data)
        })

        context = {
            'form': sample_form,
            'location_set_id': sample.location_set_id,
            'page_title': page_title,
            'sample': sample
        }

        return render_template(template_name, **context)

    sample_form = forms.SampleForm()
    if sample_form.validate_on_submit():
        sample.name = sample_form.name.data
        if sample_form.location_data.data:
            location_data = json.loads(sample_form.location_data.data)
            if location_data:
                codes = [i[0].strip() for i in location_data if i[0]]
                sample.locations = services.locations.filter(
                    models.Location.code.in_(codes),
                    models.Location.location_set_id == sample.location_set_id
                ).all()
        sample.save()

        return redirect(url_for(
            '.sample_list', location_set_id=sample.location_set_id))

    context = {
        'form': sample_form,
        'location_set_id': sample.location_set_id,
        'page_title': page_title,
        'sample': sample
    }

    return render_template(template_name, **context)


@route(bp, '/locations/set/<int:location_set_id>/export_divisions',
       methods=['GET'])
@permissions.edit_locations.require(403)
@login_required
def export_divisions(location_set_id):
    location_set = services.location_sets.fget_or_404(id=location_set_id)
    # TODO: when the representation of the graph is converted to POPOs,
    # make sure we convert to a string first
    graph = location_set.make_admin_divisions_graph()
    graph_as_bytes = json.dumps(graph, indent=2).encode()
    graph_buffer = BytesIO(graph_as_bytes)
    graph_buffer.seek(0)
    filename = 'admin-divisions-{}.json'.format(slugify_unicode(
        location_set.name))

    return send_file(graph_buffer, mimetype='application/json',
                     as_attachment=True, attachment_filename=filename)


@route(bp, '/locations/set/<int:location_set_id>/import_divisions',
       methods=['POST'])
@permissions.edit_locations.require(403)
@login_required
def import_divisions(location_set_id):
    location_set = services.location_sets.fget_or_404(id=location_set_id)
    form = forms.AdminDivisionImportForm()

    if form.validate_on_submit():
        query = services.location_types.find(
            location_set_id=location_set_id).exists()

        if not db.session.query(query).scalar():
            graph = json.load(request.files['import_file'])
            import_graph(graph, location_set, fresh_import=True)

            return redirect(url_for('.locations_builder',
                                    location_set_id=location_set_id))

    return redirect(url_for('.locations_builder',
                    location_set_id=location_set_id))
