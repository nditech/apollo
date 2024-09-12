# -*- coding: utf-8 -*-
import os

from flask import (
    Blueprint, abort, json, jsonify, redirect, render_template, request,
    session, url_for)
from flask_babel import gettext as _
from flask_security import current_user, login_required
from flask_security.utils import hash_password
from apollo import utils

from apollo.core import red, sentry, uploads
from apollo.frontend import route
from apollo.frontend.forms import file_upload_form
from apollo.users import forms, tasks
from apollo.users.models import UserUpload

bp = Blueprint('users', __name__)


@route(bp, '/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.has_role('field-coordinator'):
        abort(403)

    breadcrumbs = [_('Edit Profile')]
    user = current_user._get_current_object()
    form = forms.UserDetailsForm(instance=user)

    if form.validate_on_submit():
        data = form.data
        if data.get('password'):
            user.password = hash_password(data.get('password'))

        user.username = data.get('username')
        user.email = data.get('email')
        user.locale = data.get('locale') or None

        user.save()
        return redirect(url_for('dashboard.index'))

    context = {'form': form, 'breadcrumbs': breadcrumbs}

    return render_template('frontend/userprofile.html', **context)


@route(bp, '/user/tasks')
@login_required
def task_list():
    session_id = session.get('_id')

    # extract the data from Redis
    stringified_data = red.lrange(session_id, 0, -1)
    raw_data = [json.loads(d) for d in stringified_data]

    tasks = {
        'results': raw_data
    }

    return jsonify(tasks)


def import_users():
    form = file_upload_form(request.form)

    if not form.validate():
        return abort(400)

    user = current_user._get_current_object()
    upload_file = utils.strip_bom_header(request.files['spreadsheet'])
    filename = uploads.save(upload_file)
    upload = UserUpload(
        deployment_id=user.deployment_id, upload_filename=filename,
        user_id=user.id,
    )
    upload.save()

    return redirect(url_for('user.import_headers', upload_id=upload.id))


def import_headers(upload_id: int):
    user = current_user._get_current_object()
    upload = UserUpload.query.filter(
        UserUpload.id == upload_id, UserUpload.user == user
    ).first_or_404()
    filepath = uploads.path(upload.upload_filename)
    try:
        with open(filepath, 'rb') as source_file:
            mapping_form_class = forms.make_import_mapping_form(source_file)
    except Exception:
        sentry.captureException()

        os.remove(filepath)
        upload.delete()
        return abort(400)

    template_name = 'admin/user_headers.html'
    form = mapping_form_class()

    if request.method == 'GET':
        return render_template(template_name, form=form)
    else:
        if not form.validate():
            error_msgs = []
            if form.failed_custom_validation:
                error_msgs.append(_('Email was not mapped'))
            for key in form.errors:
                for msg in form.errors[key]:
                    error_msgs.append(msg)
            return render_template(
                'admin/user_headers_errors.html', error_msgs=error_msgs
            ), 400
    
    if 'X-Validate' not in request.headers:
        data = {}
        for field in form:
            if not field.data:
                continue
            data.update({field.data: field.label.text})

        kwargs = {
            'upload_id': upload_id,
            'mappings': data,
            'channel': session.get('_id'),
        }
        tasks.import_users.apply_async(kwargs=kwargs)

    return redirect(url_for('user.index_view'))