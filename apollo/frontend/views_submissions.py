# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import json
from flask import (
    Blueprint, jsonify, make_response, redirect, render_template, request,
    url_for, current_app
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import current_user, login_required
from flask.ext.menu import register_menu
from mongoengine import signals
from tablib import Dataset
from ..analyses.incidents import incidents_csv
from ..models import Location
from ..settings import EDIT_OBSERVER_CHECKLIST
from ..services import (
    forms, location_types, submissions, submission_comments,
    submission_versions
)
from . import route, permissions
from .filters import generate_submission_filter
from .forms import generate_submission_edit_form_class
from .helpers import (
    displayable_location_types, get_event, get_form_list_menu,
    update_data_fields)
from functools import partial

bp = Blueprint('submissions', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/submissions/form/<form_id>', methods=['GET', 'POST'])
@register_menu(bp, 'forms.checklists', _('Checklists'),
               dynamic_list_constructor=partial(get_form_list_menu,
                                                form_type='CHECKLIST'))
@register_menu(bp, 'forms.incidents', _('Critical Incidents'),
               dynamic_list_constructor=partial(get_form_list_menu,
                                                form_type='INCIDENT'))
@login_required
def submission_list(form_id):
    form = forms.get_or_404(pk=form_id)
    permissions.require_item_perm('view_forms', form)

    filter_class = generate_submission_filter(form)
    page_title = form.name
    template_name = 'frontend/submission_list.html'

    data = request.args.to_dict()
    data['form_id'] = unicode(form.pk)
    page = int(data.pop('page', 1))

    loc_types = displayable_location_types(on_submissions_view=True)

    queryset = submissions.find(
        contributor__ne=None,
        form=form
    )
    query_filterset = filter_class(queryset, request.args)
    filter_form = query_filterset.form

    if form.form_type == 'CHECKLIST':
        form_fields = []
    else:
        form_fields = [field for group in form.groups
                       for field in group.fields]

    if request.args.get('export'):
        # Export requested
        # TODO: complete export functionality
        return ""
    else:
        return render_template(
            template_name,
            args=data,
            filter_form=filter_form,
            form=form,
            form_fields=form_fields,
            location_types=loc_types,
            page_title=page_title,
            pager=query_filterset.qs.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE'))
        )


@route(bp, '/submissions/<form_id>/new', methods=['GET', 'POST'])
@permissions.add_submission.require(403)
@login_required
def submission_create(form_id):
    pass


@route(bp, '/submissions/<submission_id>', methods=['GET', 'POST'])
@permissions.edit_submission.require(403)
@login_required
def submission_edit(submission_id):
    submission = submissions.get_or_404(pk=submission_id)
    edit_form_class = generate_submission_edit_form_class(submission.form)
    page_title = _('Edit submission')
    readonly = not EDIT_OBSERVER_CHECKLIST

    if request.method == 'GET':
        submission_form = edit_form_class(
            obj=submission,
            prefix=unicode(submission.pk)
        )
        sibling_forms = [
            edit_form_class(
                obj=sibling,
                prefix=unicode(sibling.pk)
            ) for sibling in submission.siblings
        ] if submission.siblings else None
        master_form = edit_form_class(
            obj=submission.master,
            prefix=unicode(submission.master.pk)
        ) if submission.master else None

        return render_template(
            'frontend/nu_submission_edit.html',
            page_title=page_title,
            submission=submission,
            submission_form=submission_form,
            sibling_forms=sibling_forms,
            master_form=master_form,
            readonly=readonly
        )
    else:
        if submission.form.form_type == 'CHECKLIST' and not readonly:
            submission_form = edit_form_class(
                request.form,
                prefix=unicode(submission.pk)
            )
            sibling_forms = [
                edit_form_class(
                    request.form,
                    prefix=unicode(sibling.pk)
                ) for sibling in submission.siblings
            ] if submission.siblings else None
            master_form = edit_form_class(
                request.form,
                prefix=unicode(submission.master.pk)
            ) if submission.master else None

            submission_form_valid = submission_form.validate()
            master_form_valid = master_form.validate() if master_form \
                else True
            sibling_forms_valid = all(
                [s_f.validate() for s_f in sibling_forms]
            ) if sibling_forms else True

            if submission_form_valid and master_form_valid and \
                    sibling_forms_valid:

                # connect signal handler for updating submission versions
                with signals.post_save.connected_to(
                    update_submission_version,
                        sender=submissions.__model__):

                    submission_form.populate_obj(submission)
                    update_data_fields(submission)
                    submission.save()

                    if submission.siblings:
                        for sibling, sibling_form in zip(
                            submission.siblings, sibling_forms
                        ):
                            sibling_form.populate_obj(sibling)
                            update_data_fields(sibling)
                            sibling.save()

                    if submission.master:
                        master_form.populate_obj(submission.master)
                        update_data_fields(submission.master)
                        submission.master.save()
                return redirect(
                    url_for('submissions.submission_list',
                            form_id=unicode(submission.form.pk))
                    )
            else:
                print submission_form.errors
                for sibling_form in sibling_forms:
                    print sibling_form.errors
                print master_form.errors
                return render_template(
                    'frontend/nu_submission_edit.html',
                    page_title=page_title,
                    submission=submission,
                    submission_form=submission_form,
                    sibling_forms=sibling_forms,
                    master_form=master_form
                )
        else:
            submission_form = edit_form_class(
                request.form,
                prefix=unicode(submission.pk)
            )

            if submission_form.validate():
                if submission.form.form_type == 'INCIDENT':

                    # connect signal handler for save operation
                    with signals.post_save.connected_to(
                        update_submission_version,
                        sender=submissions.__model__
                    ):

                        submission_form.populate_obj(submission)
                        update_data_fields(submission)
                        submission.save()
                    return redirect(
                        url_for(
                            'submissions.submission_list',
                            form_id=unicode(submission.form.pk))
                    )
                else:
                    return redirect(
                        url_for(
                            'submissions.submission_list',
                            form_id=unicode(submission.form.pk))
                    )
            else:
                sibling_forms = [
                    edit_form_class(
                        request.form,
                        prefix=unicode(sibling.pk)
                    ) for sibling in submission.siblings
                ] if submission.siblings else None
                master_form = edit_form_class(
                    request.form,
                    prefix=unicode(submission.master.pk)
                ) if submission.master else None
                return render_template(
                    'frontend/nu_submission_edit.html',
                    page_title=page_title,
                    submission=submission,
                    submission_form=submission_form,
                    sibling_forms=sibling_forms,
                    master_form=master_form
                )


@route(bp, '/comments', methods=['POST'])
@login_required
def comment_create_view():
    submission = submissions.get_or_404(pk=request.form.get('submission'))
    comment = request.form.get('comment')
    saved_comment = submission_comments.create(
        submission=submission,
        user=current_user,
        comment=comment
    )

    return jsonify(
        comment=saved_comment.comment,
        date=saved_comment.submit_date,
        user=saved_comment.user.email
    )


def _incident_csv(form_pk, location_type_pk, location_pk=None):
    """Given an incident form id, a location type id, and optionally
    a location id, return a CSV file of the number of incidents of each
    type (form field tag) that has occurred, either for the entire
    deployment or under the given location for each location of the
    specified location type. Only submissions sent in by participants
    are used for generating the data.

    Sample output would be:

    LOC | A | B | ... | Z | TOT
    NY  | 2 | 0 | ... | 5 |  7

    `param form_pk`: a `class`Form id
    `param location_type_pk`: a `class`LocationType id
    `param location_pk`: an optional `class`Location id. if given, only
    submissions under that location will be queried.

    `returns`: a string of bytes (str) containing the CSV data.
    """
    form = forms.get_or_404(pk=form_pk, form_type='INCIDENT')
    location_type = location_types.objects.get_or_404(pk=location_type_pk)
    if location_pk:
        location = Location.objects.get_or_404(pk=location_pk)
        qs = submissions.find(contributor__ne=None, form=form) \
            .filter_in(location)
    else:
        qs = submissions.find(contributor__ne=None, form=form)

    event = get_event()
    tags = [fi.name for group in form.groups for fi in group.fields]
    qs = qs(created__lte=event.end_date, created__gte=event.start_date)
    df = qs.dataframe()
    ds = Dataset()
    ds.headers = ['LOC'] + tags + ['TOT']

    for summary in incidents_csv(df, location_type.name, tags):
        ds.append([summary.get(heading) for heading in ds.headers])

    return ds.csv


@route(bp, '/incidents/form/<form_pk>/locationtype/<location_type_pk>/incidents.csv')
@login_required
def incidents_csv_dl(form_pk, location_type_pk):
    response = make_response(
        _incident_csv(form_pk, location_type_pk))
    response.headers['Content-Type'] = 'text/csv'

    return response


@route(bp, '/incidents/form/<form_pk>/locationtype/<location_type_pk>/location/<location_pk>/incidents.csv')
@login_required
def incidents_csv_with_location_dl(form_pk, location_type_pk, location_pk):
    response = make_response(
        _incident_csv(form_pk, location_type_pk, location_pk))
    response.headers['Content-Type'] = 'text/csv'

    return response


@route(bp, '/submissions/<submission_id>/version/<version_id>')
@login_required
def submission_version(submission_id, version_id):
    submission = submissions.get_or_404(pk=submission_id)
    version = submission_versions.get_or_404(submission_version)

    return ''


def update_submission_version(sender, document, **kwargs):
    # save actual version data
    data_fields = document.form.tags
    if document.form.form_type == 'INCIDENT':
        data_fields.extend(['status', 'witness'])
    version_data = {k: document[k] for k in data_fields if k in document}

    # save user email as identity
    channel = 'Web'
    user = current_user._get_current_object()
    identity = user.email if not user.is_anonymous() else 'Unknown'

    submission_versions.create(
        submission=document,
        data=json.dumps(version_data),
        channel=channel,
        identity=identity
    )
