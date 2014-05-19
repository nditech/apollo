# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime
import json
from flask import (
    Blueprint, jsonify, make_response, redirect, render_template, request,
    url_for, current_app, abort, g
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import current_user, login_required
from flask.ext.menu import register_menu
from mongoengine import signals
from tablib import Dataset
from werkzeug.datastructures import MultiDict
from wtforms import validators
from .. import services
from ..analyses.incidents import incidents_csv
from ..tasks import send_messages
from . import route, permissions
from .filters import generate_submission_filter
from .forms import generate_submission_edit_form_class
from .helpers import (
    DictDiffer, displayable_location_types, get_event, get_form_list_menu)
from .template_filters import mkunixtimestamp
from functools import partial
from slugify import slugify_unicode

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
    form = services.forms.get_or_404(pk=form_id)
    permissions.require_item_perm('view_forms', form)

    filter_class = generate_submission_filter(form)
    page_title = form.name
    template_name = 'frontend/submission_list.html'

    data = request.args.to_dict()
    data['form_id'] = unicode(form.pk)
    page = int(data.pop('page', 1))

    loc_types = displayable_location_types(is_administrative=True)

    if request.args.get('export'):
        mode = request.args.get('export')
        if mode == 'master':
            queryset = services.submissions.find(
                submission_type='M',
                form=form
            )
        else:
            queryset = services.submissions.find(
                submission_type='O',
                form=form
            )

        query_filterset = filter_class(queryset, request.args)
        dataset = services.submissions.export_list(query_filterset.qs)
        response = make_response(
            dataset.xls
        )
        basename = slugify_unicode('%s %s %s' % (
            form.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S'),
            mode))
        response.headers['Content-Disposition'] = 'attachment; ' + \
            'filename=%s.xls' % basename
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        return response

    # first retrieve observer submissions for the form
    # NOTE: this implicitly restricts selected submissions
    # to the currently selected event.
    queryset = services.submissions.find(
        submission_type='O',
        form=form
    )
    query_filterset = filter_class(queryset, request.args)
    filter_form = query_filterset.form

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [submission.contributor.phone
                      if submission.contributor and
                      submission.contributor.phone else ''
                      for submission in query_filterset.qs]
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients:
            send_messages.delay(str(g.event.pk), message, recipients)
            return 'OK'
        else:
            abort(400)

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
    form = services.forms.get_or_404(pk=form_id, form_type='INCIDENT')
    edit_form_class = generate_submission_edit_form_class(form)
    page_title = _('Add Submission')
    template_name = 'frontend/incident_add.html'

    if request.method == 'GET':
        submission_form = edit_form_class()
        return render_template(
            template_name,
            page_title=page_title,
            form=form,
            submission_form=submission_form
        )
    else:
        submission_form = edit_form_class(request.form)

        # a small hack since we're not using modelforms,
        # these fields are required for creating a new incident
        submission_form.contributor.validators = [validators.input_required()]
        submission_form.location.validators = [validators.input_required()]

        if not submission_form.validate():
            # really should redisplay the form again
            print submission_form.errors
            return redirect(url_for(
                'submissions.submission_list', form_id=unicode(form.pk)))

        submission = services.submissions.new()
        submission_form.populate_obj(submission)

        # properly populate all fields
        submission.created = datetime.utcnow()
        submission.deployment = g.deployment
        submission.event = g.event
        submission.form = form
        submission.submission_type = 'O'
        submission.contributor = services.participants.get(
            pk=submission_form.contributor.data)
        submission.location = services.locations.get(
            pk=submission_form.location.data)

        submission.save()

        return redirect(
            url_for('submissions.submission_list', form_id=unicode(form.pk)))


@route(bp, '/submissions/<submission_id>', methods=['GET', 'POST'])
@permissions.edit_submission.require(403)
@login_required
def submission_edit(submission_id):
    submission = services.submissions.get_or_404(pk=submission_id)
    edit_form_class = generate_submission_edit_form_class(submission.form)
    page_title = _('Edit Submission')
    readonly = not g.deployment.allow_observer_submission_edit
    location_types = services.location_types.find(is_administrative=True)
    template_name = 'frontend/nu_submission_edit.html'
    comments = services.submission_comments.find(submission=submission)

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
        ]
        master_form = edit_form_class(
            obj=submission.master,
            prefix=unicode(submission.master.pk)
        ) if submission.master else None

        return render_template(
            template_name,
            page_title=page_title,
            submission=submission,
            submission_form=submission_form,
            sibling_forms=sibling_forms,
            master_form=master_form,
            readonly=readonly,
            location_types=location_types,
            comments=comments
        )
    else:
        if submission.form.form_type == 'INCIDENT':
            # no master or sibling submission here
            submission_form = edit_form_class(
                request.form, prefix=unicode(submission.pk)
            )

            if submission_form.validate():
                with signals.post_save.connected_to(
                    update_submission_version,
                    sender=services.submissions.__model__
                ):
                    form_fields = submission_form.data.keys()
                    changed = False
                    for form_field in form_fields:
                        if (
                            getattr(submission, form_field, None) !=
                            submission_form.data.get(form_field)
                        ):
                            setattr(
                                submission, form_field,
                                submission_form.data.get(form_field))
                            changed = True
                    if changed:
                        submission.save()

                if request.args.get('next'):
                    return redirect(request.args.get('next'))
                else:
                    return redirect(url_for(
                        'submissions.submission_list',
                        form_id=unicode(submission.form.pk)))
            else:
                return render_template(
                    template_name,
                    page_title=page_title,
                    submission=submission,
                    submission_form=submission_form,
                    location_types=location_types
                )
        else:
            master_form = edit_form_class(
                request.form,
                prefix=unicode(submission.master.pk)
            ) if submission.master else None

            if readonly:
                submission_form = edit_form_class(
                    obj=submission,
                    prefix=unicode(submission.pk)
                )
            else:
                submission_form = edit_form_class(
                    request.form,
                    prefix=unicode(submission.pk)
                )

            sibling_forms = [
                edit_form_class(
                    obj=sibling,
                    prefix=unicode(sibling.pk))
                for sibling in submission.siblings
            ]

            no_error = True

            # if the user is allowed to edit participant submissions,
            # everything has to be valid at one go. no partial update
            if master_form:
                if master_form.validate():
                    with signals.post_save.connected_to(
                        update_submission_version,
                        sender=services.submissions.__model__
                    ):
                        form_fields = master_form.data.keys()
                        changed = False
                        for form_field in form_fields:
                            if (
                                getattr(submission.master, form_field, None) !=
                                master_form.data.get(form_field)
                            ):
                                setattr(
                                    submission.master, form_field,
                                    master_form.data.get(form_field))
                                submission.master.overridden_fields.append(
                                    form_field)
                                changed = True
                        if changed:
                            submission.master.overridden_fields = list(set(
                                submission.master.overridden_fields))
                            submission.master.save()
                else:
                    no_error = False

            if not readonly:
                if submission_form.validate():
                    with signals.post_save.connected_to(
                        update_submission_version,
                        sender=services.submissions.__model__
                    ):
                        form_fields = submission_form.data.keys()
                        changed = False
                        for form_field in form_fields:
                            if (
                                getattr(submission, form_field, None) !=
                                submission_form.data.get(form_field)
                            ):
                                setattr(
                                    submission, form_field,
                                    submission_form.data.get(form_field))
                                changed = True
                        if changed:
                            submission.save()
                else:
                    no_error = False

            if no_error:
                if request.args.get('next'):
                    return redirect(request.args.get('next'))
                else:
                    return redirect(url_for(
                        'submissions.submission_list',
                        form_id=unicode(submission.form.pk)
                    ))
            else:
                return render_template(
                    template_name,
                    page_title=page_title,
                    submission=submission,
                    submission_form=submission_form,
                    master_form=master_form,
                    sibling_forms=sibling_forms,
                    readonly=readonly,
                    location_types=location_types,
                    comments=comments
                )


@route(bp, '/comments', methods=['POST'])
@permissions.edit_submission.require(403)
@login_required
def comment_create_view():
    submission = services.submissions.get_or_404(
        pk=request.form.get('submission'))
    comment = request.form.get('comment')
    saved_comment = services.submission_comments.create(
        submission=submission,
        user=current_user._get_current_object(),
        comment=comment,
        submit_date=datetime.utcnow()
    )

    return jsonify(
        comment=saved_comment.comment,
        date=mkunixtimestamp(saved_comment.submit_date),
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
    form = services.forms.get_or_404(pk=form_pk, form_type='INCIDENT')
    location_type = services.location_types.objects.get_or_404(
        pk=location_type_pk)
    if location_pk:
        location = services.locations.get_or_404(pk=location_pk)
        qs = services.submissions.find(submission_type='O', form=form) \
            .filter_in(location)
    else:
        qs = services.submissions.find(submission_type='O', form=form)

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
    submission = services.submissions.get_or_404(pk=submission_id)
    version = services.submission_versions.get_or_404(
        pk=version_id, submission=submission)
    form = submission.form
    form_data = MultiDict(json.loads(version.data))
    page_title = _('View submission')
    template_name = 'frontend/submission_history.html'

    diff = DictDiffer(submission._data, form_data)

    return render_template(
        template_name,
        page_title=page_title,
        diff=diff,
        form=form,
        submission=submission,
        submission_version=version,
        data=form_data
    )


def verification_list(form_id):
    form = services.forms.get_or_404(pk=form_id, form_type='CHECKLIST')
    queryset = services.submissions.find(form=form, submission_type='M')

    context = {}

    return ''


def update_submission_version(sender, document, **kwargs):
    if sender != services.submissions.__model__:
        return

    # save actual version data
    data_fields = document.form.tags
    if document.form.form_type == 'INCIDENT':
        data_fields.extend(['status', 'witness'])
    version_data = {k: document[k] for k in data_fields if k in document}

    # save user email as identity
    channel = 'WEB'
    user = current_user._get_current_object()
    identity = user.email if not user.is_anonymous() else 'unknown'

    services.submission_versions.create(
        submission=document,
        data=json.dumps(version_data),
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity
    )
