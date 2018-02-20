# -*- coding: utf-8 -*-
import csv
from datetime import datetime
import json
try:
    from io import StringIO
except ImportError:
    from io import StringIO
from flask import (
    Blueprint, jsonify, make_response, redirect, render_template, request,
    url_for, current_app, abort, g, Response
)
from flask_babelex import lazy_gettext as _
from flask_security import current_user, login_required
from flask_security.utils import verify_and_update_password
from flask_menu import register_menu
from flask_httpauth import HTTPBasicAuth
from tablib import Dataset

from werkzeug.datastructures import MultiDict
from apollo import models, services, utils
from apollo.submissions.incidents import incidents_csv
from apollo.participants.utils import update_participant_completion_rating
from apollo.submissions.aggregation import (
    aggregated_dataframe, _quality_check_aggregation)
from apollo.submissions.models import QUALITY_STATUSES, Submission
from apollo.submissions.recordmanagers import AggFrameworkExporter
from apollo.messaging.tasks import send_messages
from apollo.frontend import route, permissions
from apollo.frontend.filters import generate_submission_filter
from apollo.frontend.filters import generate_quality_assurance_filter
from apollo.frontend.forms import generate_submission_edit_form_class
from apollo.frontend.helpers import (
    DictDiffer, displayable_location_types, get_event,
    get_form_list_menu, get_quality_assurance_form_list_menu,
    get_quality_assurance_form_dashboard_menu)
from apollo.frontend.template_filters import mkunixtimestamp
from functools import partial
from slugify import slugify_unicode


auth = HTTPBasicAuth()
bp = Blueprint('submissions', __name__, template_folder='templates',
               static_folder='static')


SUB_VERIFIED = '4'


def get_valid_values(choices):
    return [i[0] for i in choices]


@auth.verify_password
def verify_pw(username, password):
    user = services.users.find(email=username).first()

    if not user:
        return False

    return verify_and_update_password(password, user)


@route(bp, '/submissions/form/<form_id>', methods=['GET', 'POST'])
@register_menu(
    bp, 'main.checklists',
    _('Checklists'), order=1, icon='<i class="glyphicon glyphicon-check"></i>',
    visible_when=lambda: len(get_form_list_menu(form_type='CHECKLIST')) > 0)
@register_menu(bp, 'main.checklists.forms', _('Checklists'),
               dynamic_list_constructor=partial(
               get_form_list_menu, form_type='CHECKLIST'))
@register_menu(
    bp, 'main.incidents',
    _('Critical Incidents'),
    order=2, icon='<i class="glyphicon glyphicon-check"></i>',
    visible_when=lambda: len(get_form_list_menu(form_type='INCIDENT')) > 0)
@register_menu(bp, 'main.incidents.forms', _('Critical Incidents'),
               dynamic_list_constructor=partial(
               get_form_list_menu, form_type='INCIDENT'))
@login_required
def submission_list(form_id):
    form = services.forms.find(
        id=form_id).first_or_404()
    permissions.require_item_perm('view_forms', form)

    filter_class = generate_submission_filter(form)
    page_title = form.name
    template_name = 'frontend/submission_list.html'

    data = request.args.to_dict(flat=False)
    data['form_id'] = str(form.id)
    page_spec = data.pop('page', None) or [1]
    page = int(page_spec[0])

    loc_types = displayable_location_types(is_administrative=True)

    location = None
    if request.args.get('location'):
        location = services.locations.find(
            id=request.args.get('location')).first()

    if request.args.get('export') and permissions.export_submissions.can():
        mode = request.args.get('export')
        if mode in ['master', 'aggregated']:
            # TODO: this query was ordered by location
            queryset = services.submissions.find(
                submission_type='M',
                form=form
            )
        else:
            # TODO: this query was ordered by location, then participant
            queryset = services.submissions.find(
                submission_type='O',
                form=form
            )

        # TODO: fix this. no exports yet. nor aggregation
        query_filterset = filter_class(queryset, request.args)
        basename = slugify_unicode('%s %s %s %s' % (
            g.event.name.lower(),
            form.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S'),
            mode))
        content_disposition = 'attachment; filename=%s.csv' % basename
        if mode == 'aggregated':
            # TODO: you want to change the float format or even remove it
            # if you have columns that have float values
            exporter = AggFrameworkExporter(query_filterset.qs)
            records, headers = exporter.export_dataset()

            export_buffer = StringIO()
            writer = csv.DictWriter(export_buffer, headers)
            writer.writeheader()
            for record in records:
                writer.writerow(record)

            dataset = export_buffer.getvalue()
        else:
            dataset = services.submissions.export_list(
                query_filterset.qs, g.deployment)

        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )

    # first retrieve observer submissions for the form
    # NOTE: this implicitly restricts selected submissions
    # to the currently selected event.
    # TODO: this query was ordered by location, then participant
    queryset = services.submissions.find(
        submission_type='O',
        form=form
    )
    query_filterset = filter_class(queryset, request.args)
    filter_form = query_filterset.form

    # TODO: rewrite this. verify what select_related does
    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [x for x in [submission.participant.phone
                if submission.participant and
                submission.participant.phone else ''
                for submission in query_filterset.qs.with_entities(
                    models.Submission.participant).select_related(1)] if x is not '']
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients and permissions.send_messages.can():
            send_messages.delay(str(g.event.id), message, recipients)
            return 'OK'
        else:
            abort(400)

    if form.form_type == 'CHECKLIST':
        form_fields = []
    else:
        form_fields = [field for group in form.groups
                       for field in group.fields if not field.is_comment_field]

    return render_template(
        template_name,
        args=data,
        filter_form=filter_form,
        form=form,
        form_fields=form_fields,
        location_types=loc_types,
        location=location,
        page_title=page_title,
        pager=query_filterset.qs.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE'))
    )


@route(bp, '/submissions/<form_id>/new', methods=['GET', 'POST'])
@permissions.add_submission.require(403)
@login_required
def submission_create(form_id):
    form = services.forms.find(
        id=form_id, form_type='INCIDENT').first_or_404()
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

        if not submission_form.validate():
            # really should redisplay the form again
            return redirect(url_for(
                'submissions.submission_list', form_id=str(form.id)))

        # TODO: fix this. can't populate the submission
        # directly
        submission = models.Submission()
        submission_form.populate_obj(submission)

        # properly populate all fields
        submission.created = datetime.utcnow()
        submission.deployment = g.deployment
        submission.event = g.event
        submission.form = form
        submission.submission_type = 'O'
        submission.contributor = submission_form.contributor.data
        submission.location = submission_form.location.data
        if not submission.location:
            submission.location = submission.contributor.location

        submission.save()

        return redirect(
            url_for('submissions.submission_list', form_id=str(form.id)))


@route(bp, '/submissions/<submission_id>', methods=['GET', 'POST'])
@permissions.edit_submission.require(403)
@login_required
def submission_edit(submission_id):
    submission = services.submissions.find(id=submission_id)
    edit_form_class = generate_submission_edit_form_class(submission.form)
    page_title = _('Edit Submission')
    readonly = not g.deployment.allow_observer_submission_edit
    location_types = services.location_types.find(is_administrative=True)
    template_name = 'frontend/submission_edit.html'
    comments = services.submission_comments.find(submission=submission)

    if request.method == 'GET':
        submission_form = edit_form_class(
            obj=submission,
            prefix=str(submission.id)
        )
        sibling_forms = [
            edit_form_class(
                obj=sibling,
                prefix=str(sibling.id)
            ) for sibling in submission.siblings
        ]
        master_form = edit_form_class(
            obj=submission.master,
            prefix=str(submission.master.id)
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
                request.form, prefix=str(submission.id)
            )

            if submission_form.validate():
                form_fields = list(submission_form.data.keys())
                changed = False
                for form_field in form_fields:
                    field_value = submission_form.data.get(form_field)
                    if field_value is None:
                        continue

                    if submission.data.get(form_field) != field_value:
                        submission.data[form_field] = field_value
                        changed = True
                if changed:
                    submission.save()
                    update_submission_version(submission)

                if request.form.get('next'):
                    return redirect(request.form.get('next'))
                else:
                    return redirect(url_for(
                        'submissions.submission_list',
                        form_id=str(submission.form.id)))
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
                prefix=str(submission.master.id)
            ) if submission.master else None

            submission_form = edit_form_class(
                request.form,
                obj=submission,
                prefix=str(submission.id)
            )

            sibling_forms = [
                edit_form_class(
                    obj=sibling,
                    prefix=str(sibling.id))
                for sibling in submission.siblings
            ]

            no_error = True

            selection = request.form.get('submission_selection', None)
            if not selection and readonly:
                selection = 'ps'
            elif not selection and not readonly:
                selection = 'obs'

            # if the user is allowed to edit participant submissions,
            # everything has to be valid at one go. no partial update
            if master_form and selection == 'ps':
                if master_form.validate():
                    form_fields = list(master_form.data.keys())
                    changed = False
                    for form_field in form_fields:
                        # we've had issues with quarantine and verification statuses
                        # previously. this explicitly deals with that
                        if form_field == 'verification_status':
                            new_verification_status = master_form.data.get(form_field)
                            if new_verification_status not in get_valid_values(Submission.VERIFICATION_STATUSES):
                                continue
                            else:
                                if getattr(submission.master, form_field) != new_verification_status:
                                    changed = True
                                    setattr(submission.master, form_field, new_verification_status)
                                continue

                        if form_field == 'quarantine_status':
                            new_quarantine_status = master_form.data.get(form_field)
                            if new_quarantine_status not in get_valid_values(Submission.QUARANTINE_STATUSES):
                                continue
                            else:
                                if getattr(submission.master, form_field) != new_quarantine_status:
                                    changed = True
                                    setattr(submission.master, form_field, new_quarantine_status)
                                continue
                        if (
                            getattr(submission.master, form_field, None) !=
                            master_form.data.get(form_field)
                        ):
                            if (
                                not master_form.data.get(form_field) and
                                isinstance(master_form.data.get(
                                    form_field), list)
                            ):
                                setattr(
                                    submission.master, form_field,
                                    None)
                            else:
                                setattr(
                                    submission.master, form_field,
                                    master_form.data.get(form_field))

                            if (
                                form_field not in
                                ["quarantine_status",
                                    "verification_status"]
                            ):
                                submission.master.overridden_fields.append(
                                    form_field)
                            changed = True
                    if changed:
                        submission.master.overridden_fields = list(set(
                            submission.master.overridden_fields))
                        submission.master.save()
                        update_submission_version(submission)
                else:
                    no_error = False

            if selection == 'obs':
                if submission_form.validate():
                    changed = False

                    form_fields = list(submission_form.data.keys())
                    for form_field in form_fields:
                        # we've had issues with quarantine and verification statuses
                        # previously. this explicitly deals with that
                        if form_field == 'verification_status':
                            new_verification_status = submission_form.data.get(form_field)
                            if new_verification_status not in get_valid_values(Submission.VERIFICATION_STATUSES):
                                continue
                            else:
                                if getattr(submission, form_field) != new_verification_status:
                                    changed = True
                                    setattr(submission, form_field, new_verification_status)
                                continue

                        if form_field == 'quarantine_status':
                            new_quarantine_status = submission_form.data.get(form_field)
                            if new_quarantine_status not in get_valid_values(Submission.QUARANTINE_STATUSES):
                                continue
                            else:
                                if getattr(submission, form_field) != new_quarantine_status:
                                    changed = True
                                    setattr(submission, form_field, new_quarantine_status)
                                continue
                        if (
                            getattr(submission, form_field, None) !=
                            submission_form.data.get(form_field)
                        ):
                            if (
                                not submission_form.data.get(
                                    form_field) and
                                isinstance(submission_form.data.get(
                                    form_field), list)
                            ):
                                setattr(
                                    submission, form_field,
                                    None)
                            else:
                                setattr(
                                    submission, form_field,
                                    submission_form.data.get(form_field))
                            changed = True
                    if changed:
                        submission.save()
                        update_submission_version(submission)
                    # submission is for a checklist form, update
                    # contributor completion rating
                    update_participant_completion_rating(
                        submission.contributor)
            else:
                no_error = False

            if no_error:
                if request.form.get('next'):
                    return redirect(request.form.get('next'))
                else:
                    return redirect(url_for(
                        'submissions.submission_list',
                        form_id=str(submission.form.id)
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
        id=request.form.get('submission'))
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
    form = services.forms.get_or_404(id=form_pk, form_type='INCIDENT')
    location_type = services.location_types.objects.get_or_404(
        id=location_type_pk)
    if location_pk:
        location = services.locations.get_or_404(id=location_pk)
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
    submission = services.submissions.get_or_404(id=submission_id)
    version = services.submission_versions.get_or_404(
        id=version_id, submission=submission)
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


@route(bp, '/dashboard/qa/<form_id>')
@register_menu(
    bp, 'main.dashboard.qa', _('Quality Assurance'),
    icon='<i class="glyphicon glyphicon-tasks"></i>', order=1,
    visible_when=lambda: len(
        get_quality_assurance_form_dashboard_menu(
            form_type='CHECKLIST', quality_checks_enabled=True)) > 0 \
        and permissions.view_quality_assurance.can(),
    dynamic_list_constructor=partial(
        get_quality_assurance_form_dashboard_menu,
        form_type='CHECKLIST', verifiable=True))
@permissions.view_quality_assurance.require(403)
@login_required
def quality_assurance_dashboard(form_id):
    form = services.forms.get_or_404(id=form_id, form_type='CHECKLIST')
    page_title = _('Quality Assurance — %(name)s', name=form.name)
    filter_class = generate_quality_assurance_filter(form)
    data = request.args.to_dict()
    data['form_id'] = str(form.id)
    loc_types = displayable_location_types(is_administrative=True)

    location = None
    if request.args.get('location'):
        location = services.locations.find(
            id=request.args.get('location')).first()

    submissions = services.submissions.find(form=form, submission_type='O')
    query_filterset = filter_class(submissions, request.args)
    filter_form = query_filterset.form

    # get individual check data
    check_data = _quality_check_aggregation(query_filterset.qs, form)

    template_name = 'frontend/quality_assurance_dashboard.html'

    context = {
        'filter_form': filter_form,
        'form': form,
        'args': data,
        'location_types': loc_types,
        'location': location,
        'page_title': page_title,
        'check_data': check_data
    }

    return render_template(template_name, **context)


@route(bp, '/submissions/qa/<form_id>/list')
@register_menu(
    bp, 'main.qa',
    _('Quality Assurance'),
    order=3, icon='<i class="glyphicon glyphicon-ok"></i>',
    visible_when=lambda: len(get_quality_assurance_form_list_menu(
        form_type='CHECKLIST', quality_checks_enabled=True)) > 0 and
    permissions.view_quality_assurance.can())
@register_menu(
    bp, 'main.qa.checklists', _('Quality Assurance'),
    icon='<i class="glyphicon glyphicon-ok"></i>', order=1,
    dynamic_list_constructor=partial(
        get_quality_assurance_form_list_menu,
        form_type='CHECKLIST', verifiable=True))
@permissions.view_quality_assurance.require(403)
@login_required
def quality_assurance_list(form_id):
    form = services.forms.get_or_404(
        models.Form.id == form_id,
        models.Form.form_type == 'CHECKLIST')
    page_title = _('Quality Assurance — %(name)s', name=form.name)
    filter_class = generate_quality_assurance_filter(form)
    data = request.args.to_dict()
    data['form_id'] = str(form.id)
    page = int(data.pop('page', 1))
    loc_types = displayable_location_types(is_administrative=True)

    location = None
    if request.args.get('location'):
        location = services.locations.find(
            id=request.args.get('location')).first()

    if request.args.get('export') and permissions.export_submissions.can():
        mode = request.args.get('export')
        queryset = services.submissions.find(
            submission_type='O',
            form=form
        ).order_by('location', 'contributor')

        query_filterset = filter_class(queryset, request.args)
        dataset = services.submissions.export_list(
            query_filterset.qs, g.deployment)
        basename = slugify_unicode('%s %s %s %s' % (
            g.event.name.lower(),
            form.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S'),
            mode))
        content_disposition = 'attachment; filename=%s.csv' % basename

        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )

    submissions = services.submissions.find(form=form, submission_type='O')
    query_filterset = filter_class(submissions, request.args)
    filter_form = query_filterset.form
    VERIFICATION_OPTIONS = services.submissions.__model__.VERIFICATION_OPTIONS

    context = {
        'form': form,
        'args': data,
        'filter_form': filter_form,
        'page_title': page_title,
        'location_types': loc_types,
        'location': location,
        'pager': query_filterset.qs.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE')),
        'submissions': submissions,
        'quality_statuses': QUALITY_STATUSES,
        'verification_statuses': VERIFICATION_OPTIONS
    }

    template_name = 'frontend/quality_assurance_list.html'

    return render_template(template_name, **context)


def update_submission_version(document):
    # save actual version data
    data_fields = document.form.tags
    if document.form.form_type == 'INCIDENT':
        data_fields.extend(['status'])
    version_data = {k: document[k] for k in data_fields if k in document}

    # get previous version
    previous = services.submission_versions.find(
        submission=document).order_by('-timestamp').first()

    if previous:
        prev_data = json.loads(previous.data)
        diff = DictDiffer(version_data, prev_data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

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


@route(bp, '/api/v1/submissions/export/aggregated/<form_id>')
@auth.login_required
def submission_export(form_id):
    form = services.forms.get_or_404(id=form_id)

    queryset = services.submissions.find(
        form=form, submission_type='M').order_by('location')
    dataset = aggregated_dataframe(queryset, form).to_csv(
        encoding='utf-8', index=False, float_format='%d')

    # TODO: any other way to control/stream the output?
    # currently it just takes the name of the form ID
    return Response(
        dataset,
        mimetype='text/csv')
