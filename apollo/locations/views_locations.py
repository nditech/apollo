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
from sqlalchemy.orm.attributes import flag_modified

from apollo import services, utils
from apollo.core import db, sentry, uploads
from apollo.frontend import permissions, route
from apollo.frontend.forms import (
    file_upload_form, generate_location_edit_form,
    DummyForm)
from apollo.locations import api, filters, forms, tasks
from apollo.locations.utils import import_graph
from .models import LocationSet, LocationType, Location, LocationTranslations
from .models import LocationTypePath, LocationDataField
from ..users.models import UserUpload


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


def locations_list(view, location_set_id):
    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first_or_404()
    queryset = Location.query.select_from(
        Location, LocationTranslations).filter(
            Location.location_set_id == location_set_id)
    queryset_filter = filters.location_filterset(
        location_set_id=location_set_id)(queryset, request.args)
    extra_fields = [
        field for field in LocationDataField.query.filter(
            LocationDataField.location_set_id == location_set_id)
        if field.visible_in_lists]

    template_name = 'admin/locations_list.html'
    breadcrumbs = [
        {'text': _('Location Sets'), 'url': url_for('locationset.index_view')},
        location_set.name, _('Locations')]

    args = request.args.to_dict(flat=False)
    args.update(location_set_id=location_set_id)
    page = int(args.pop('page', [1])[0])

    # NOTE: this was ordered by location type
    subset = queryset_filter.qs.order_by(Location.code).distinct(Location.code)

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
            breadcrumbs=breadcrumbs,
            form=DummyForm(),
            location_set=location_set,
            location_set_id=location_set_id,
            locations=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE')))

        return view.render(template_name, **ctx)


def location_edit(view, id):
    template_name = 'admin/location_edit.html'
    location = Location.query.filter_by(id=id).first_or_404()
    breadcrumbs = [
        {'text': _('Location Sets'), 'url': url_for('locationset.index_view')},
        location.location_set.name, _('Edit Location')]

    if request.method == 'GET':
        form = generate_location_edit_form(location)
    else:
        form = generate_location_edit_form(location, request.form)

        if form.validate():
            location.name = form.name.data
            location.lat = form.lat.data
            location.lon = form.lon.data

            # note: if only .name is changed, SQLA does not register
            # the object as being dirty or needing an update so we
            # force it to recognize the object as needing an update.
            flag_modified(location, 'name_translations')
            location.save()

            return redirect(url_for(
                'locationset.locations_list',
                location_set_id=location.location_set_id))

    return view.render(
        template_name, form=form, breadcrumbs=breadcrumbs,
        location_set=location.location_set)


def locations_import(location_set_id):
    form = file_upload_form(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        upload_file = utils.strip_bom_header(request.files['spreadsheet'])
        filename = uploads.save(upload_file)
        upload = UserUpload(
            deployment_id=g.deployment.id, upload_filename=filename,
            user_id=user.id)
        upload.save()

        return redirect(url_for('locationset.locations_headers',
                                location_set_id=location_set_id,
                                upload_id=upload.id))


def locations_headers(view, location_set_id, upload_id):
    user = current_user._get_current_object()
    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first_or_404()

    # disallow processing other users' files
    upload = UserUpload.query.filter(
        UserUpload.id == upload_id, UserUpload.user == user).first_or_404()
    filepath = uploads.path(upload.upload_filename)
    try:
        with open(filepath, 'rb') as source_file:
            mapping_form_class = forms.make_import_mapping_form(
                source_file, location_set)
    except Exception:
        # log exception (if Sentry is enabled)
        sentry.captureException()

        # delete loaded file
        os.remove(filepath)
        upload.delete()
        return abort(400)

    template_name = 'admin/location_headers.html'

    if request.method == 'GET':
        form = mapping_form_class()
        return view.render(template_name, form=form)
    else:
        form = mapping_form_class()

        if not form.validate():
            error_msgs = []
            for key in form.errors:
                for msg in form.errors[key]:
                    error_msgs.append(msg)
            return view.render(
                'admin/location_headers_errors.html',
                error_msgs=error_msgs), 400
        else:
            if 'X-Validate' not in request.headers:
                # get header mappings
                data = {
                    field.data: field.label.text
                    for field in form if field.data
                }

                # invoke task asynchronously
                kwargs = {
                    'upload_id': upload.id,
                    'mappings': data,
                    'location_set_id': location_set_id
                }
                tasks.import_locations.apply_async(kwargs=kwargs)

            return redirect(url_for('locationset.locations_list',
                                    location_set_id=location_set_id))


def locations_builder(view, location_set_id):
    location_set = LocationSet.query.get_or_404(location_set_id)

    has_admin_divisions = db.session.query(LocationType.query.filter(
        LocationType.location_set_id == location_set_id).exists()).scalar()

    template_name = 'admin/administrative_divisions.html'
    breadcrumbs = [
        {'text': _('Location Sets'), 'url': url_for('locationset.index_view')},
        location_set.name, _('Administrative Divisions')]
    form = forms.AdminDivisionImportForm()

    if request.method == 'POST' and request.form.get('divisions_graph'):
        divisions_graph = json.loads(request.form.get('divisions_graph'))
        nodes = divisions_graph.get('nodes')

        # find any divisions that were not included in the saved graph
        # and delete them if there are no linked locations
        saved_node_ids = [node.get('id') for node in nodes
                          if str(node.get('id')).isdigit()]
        unused_location_types = LocationType.query.filter(
            LocationType.location_set_id == location_set_id,
            not_(LocationType.id.in_(saved_node_ids))
        ).all()

        for unused_lt in unused_location_types:
            query = Location.query.filter(Location.location_type == unused_lt)
            if db.session.query(query.exists()).scalar():
                flash(_('Administrative level %(name)s has locations assigned '
                        'and cannot be deleted.', name=unused_lt.name),
                      category='danger')
                continue

            # explicitly doing this because we didn't add a cascade
            # to the backref
            LocationTypePath.query.filter(or_(
                LocationTypePath.ancestor_id == unused_lt.id,
                LocationTypePath.descendant_id == unused_lt.id
            )).delete()
            unused_lt.delete()

        import_graph(divisions_graph, location_set)

        flash(
            _('Your changes have been saved.'),
            category='info'
        )

    return view.render(
        template_name, breadcrumbs=breadcrumbs, location_set=location_set,
        form=form, has_admin_divisions=has_admin_divisions)


def export_divisions(location_set_id):
    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first_or_404()
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


def import_divisions(location_set_id):
    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first_or_404()
    form = forms.AdminDivisionImportForm()

    if form.validate_on_submit():
        query = LocationType.query.filter(
            LocationType.location_set_id == location_set_id).exists()

        if not db.session.query(query).scalar():
            graph = json.load(request.files['import_file'])
            import_graph(graph, location_set, fresh_import=True)

            return redirect(url_for('locationset.builder',
                                    location_set_id=location_set_id))

    return redirect(url_for('locationset.builder',
                    location_set_id=location_set_id))
