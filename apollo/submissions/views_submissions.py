# -*- coding: utf-8 -*-
import codecs
import csv
from datetime import datetime
from functools import partial
from io import StringIO

from flask import (
    Blueprint, Response, abort, current_app, g, jsonify, make_response,
    redirect, render_template, request, stream_with_context, url_for
)
from flask_babelex import lazy_gettext as _
from flask_httpauth import HTTPBasicAuth
from flask_menu import register_menu
from flask_security import current_user, login_required
from flask_security.utils import verify_and_update_password
from sqlalchemy.dialects.postgresql import array
from tablib import Dataset
from werkzeug.datastructures import MultiDict

from apollo import models, services, utils
from apollo.core import db
from apollo.frontend import route, permissions
from apollo.frontend.filters import generate_quality_assurance_filter
from apollo.frontend.helpers import (
    DictDiffer, displayable_location_types, get_event,
    get_form_list_menu, get_quality_assurance_form_list_menu,
    get_quality_assurance_form_dashboard_menu)
from apollo.frontend.template_filters import mkunixtimestamp
from apollo.messaging.tasks import send_messages
from apollo.participants.utils import update_participant_completion_rating
from apollo.submissions import filters, forms
from apollo.submissions.incidents import incidents_csv
from apollo.submissions.aggregation import (
    aggregated_dataframe, _qa_counts)
from apollo.submissions.models import QUALITY_STATUSES, Submission
from apollo.submissions.qa.query_builder import get_inline_qa_status
from apollo.submissions.recordmanagers import AggFrameworkExporter
from apollo.submissions.utils import make_submission_dataframe
from slugify import slugify_unicode


auth = HTTPBasicAuth()
bp = Blueprint('submissions', __name__, template_folder='templates',
               static_folder='static')


SUB_VERIFIED = '4'


def get_valid_values(choices):
    return [i[0] for i in choices]


@auth.verify_password
def verify_pw(username, password):
    deployment = g.deployment
    user = services.users.find(deployment=deployment, email=username).first()

    if not user:
        return False

    return verify_and_update_password(password, user)


@route(bp, '/submissions/form/<int:form_id>', methods=['GET', 'POST'])
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
    event = g.event
    form = services.forms.find(
        id=form_id, form_set_id=event.form_set_id).first_or_404()
    permissions.can_access_resource(form)

    filter_class = filters.make_submission_list_filter(event, form)
    page_title = form.name
    template_name = 'frontend/submission_list.html'

    data = request.args.to_dict(flat=False)
    data['form_id'] = str(form.id)
    page_spec = data.pop('page', None) or [1]
    page = int(page_spec[0])

    loc_types = displayable_location_types(
        is_administrative=True, location_set_id=event.location_set_id)

    location = None
    if request.args.get('location'):
        location = services.locations.find(
            location_set_id=event.location_set_id,
            id=request.args.get('location')).first()

    if request.args.get('export') and permissions.export_submissions.can():
        mode = request.args.get('export')
        if mode in ['master', 'aggregated']:
            queryset = services.submissions.find(
                submission_type='M',
                form=form, event=event
            ).join(
                models.Location,
                models.Submission.location_id == models.Location.id
            ).order_by(models.Location.code)
        else:
            queryset = services.submissions.find(
                submission_type='O',
                form=form, event=event
            ).join(
                models.Location,
                models.Submission.location_id == models.Location.id
            ).join(
                models.Participant,
                models.Submission.participant_id == models.Participant.id
            ).order_by(models.Location.code, models.Participant.participant_id)

        # TODO: fix this. no exports yet. nor aggregation
        # query_filterset = filter_class(queryset, request.args)
        basename = slugify_unicode('%s %s %s %s' % (
            g.event.name.lower(),
            form.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S'),
            mode))
        content_disposition = 'attachment; filename=%s.csv' % basename
        if mode == 'aggregated':
            # TODO: you want to change the float format or even remove it
            # if you have columns that have float values
            # exporter = AggFrameworkExporter(query_filterset.qs)
            exporter = AggFrameworkExporter(queryset)
            records, headers = exporter.export_dataset()

            export_buffer = StringIO()
            writer = csv.DictWriter(export_buffer, headers)
            writer.writeheader()
            for record in records:
                writer.writerow(record)

            dataset = export_buffer.getvalue()
        else:
            dataset = services.submissions.export_list(
                # query_filterset.qs)
                queryset)

        return Response(
            stream_with_context(dataset),
            headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )

    # first retrieve observer submissions for the form
    # NOTE: this implicitly restricts selected submissions
    # to the currently selected event.
    queryset = services.submissions.find(
        submission_type='O',
        form=form,
        event_id=event.id
    ).join(
        models.Location,
        models.Submission.location_id == models.Location.id
    ).join(
        models.Participant,
        models.Submission.participant_id == models.Participant.id
    ).order_by(models.Location.code, models.Participant.participant_id)

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
            send_messages.delay(event.id, message, recipients)
            return 'OK'
        else:
            abort(400)

    if form.form_type == 'CHECKLIST':
        form_fields = []
    else:
        if form.data and 'groups' in form.data:
            form_fields = [
                field for group in form.data['groups']
                for field in group['fields'] if not field.get('is_comment')]
        else:
            form_fields = []

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


@route(bp, '/submissions/<int:form_id>/new', methods=['GET', 'POST'])
@permissions.add_submission.require(403)
@login_required
def submission_create(form_id):
    event = g.event
    questionnaire_form = services.forms.find(
        id=form_id, form_type='INCIDENT', form_set_id=event.form_set_id
    ).first_or_404()
    edit_form_class = forms.make_submission_edit_form_class(
        event, questionnaire_form)
    page_title = _('Add Submission')
    template_name = 'frontend/incident_add.html'

    if request.method == 'GET':
        submission_form = edit_form_class()
        return render_template(
            template_name,
            page_title=page_title,
            form=questionnaire_form,
            submission_form=submission_form
        )
    else:
        submission_form = edit_form_class(request.form)

        # a small hack since we're not using modelforms,
        # these fields are required for creating a new incident

        if not submission_form.validate():
            # really should redisplay the form again
            return render_template(
                template_name,
                page_title=page_title,
                form=questionnaire_form,
                submission_form=submission_form
            )

        data_fields = set(submission_form.data.keys()).intersection(
            questionnaire_form.tags)

        data = {
            k: submission_form.data.get(k)
            for k in data_fields
            if submission_form.data.get(k) is not None}

        submission = models.Submission(
            event_id=event.id,
            deployment_id=event.deployment_id,
            form_id=form_id,
            submission_type='O',
            created=utils.current_timestamp(),
            data=data
        )

        # properly populate all fields
        # either the participant or the location may be blank, but not both
        if submission_form.participant.data:
            submission.participant = submission_form.participant.data
            submission.location = submission.participant.location

        if submission_form.location.data:
            submission.location = submission_form.location.data

        submission.incident_status = submission_form.status.data
        submission.save()

        return redirect(
            url_for('submissions.submission_list', form_id=form_id))


@route(bp, '/submissions/<int:submission_id>', methods=['GET', 'POST'])
@permissions.edit_submission.require(403)
@login_required
def submission_edit(submission_id):
    event = g.event
    submission = services.submissions.find(
        event_id=event.id, id=submission_id).first_or_404()
    questionnaire_form = submission.form
    edit_form_class = forms.make_submission_edit_form_class(
        event, submission.form)
    page_title = _('Edit Submission')
    readonly = not g.deployment.allow_observer_submission_edit
    location_types = services.location_types.find(
        location_set_id=event.location_set_id,
        is_administrative=True)
    template_name = 'frontend/submission_edit.html'
    comments = services.submission_comments.find(submission=submission)

    sibling_submissions = submission.siblings
    master_submission = submission.master

    if request.method == 'GET':
        initial_data = submission.data.copy() if submission.data else {}
        initial_data.update(location=submission.location_id)
        initial_data.update(participant=submission.participant_id)
        failed_checks = []

        if questionnaire_form.form_type == 'INCIDENT':
            initial_data.update(description=submission.incident_description)
            if submission.incident_status:
                initial_data.update(status=submission.incident_status.code)
        else:
            if questionnaire_form.quality_checks_enabled:
                for check in questionnaire_form.quality_checks:
                    result = get_inline_qa_status(submission, check)
                    if result is False:
                        failed_checks.append(check['description'])

        submission_form = edit_form_class(
            data=initial_data,
            prefix=str(submission.id)
        )
        sibling_forms = [
            edit_form_class(
                data=sibling.data,
                prefix=str(sibling.id)
            ) for sibling in sibling_submissions
        ]
        if master_submission:
            master_form = edit_form_class(
                data=master_submission.data,
                prefix=str(master_submission.id)
            )
        else:
            master_form = None

        return render_template(
            template_name,
            page_title=page_title,
            submission=submission,
            submission_form=submission_form,
            sibling_forms=sibling_forms,
            master_form=master_form,
            readonly=readonly,
            location_types=location_types,
            comments=comments,
            failed_checks=failed_checks
        )
    else:
        if questionnaire_form.form_type == 'INCIDENT':
            # no master or sibling submission here
            submission_form = edit_form_class(
                request.form, prefix=str(submission.id)
            )

            if submission_form.validate():
                form_fields = submission_form.data.keys()
                data_fields = set(form_fields).intersection(
                    questionnaire_form.tags)
                data = submission.data.copy()
                update_params = {}
                changed = False
                for form_field in data_fields:
                    field_value = submission_form.data.get(form_field)
                    if field_value is None:
                        continue

                    if submission.data.get(form_field) != field_value:
                        data[form_field] = field_value
                        changed = True

                new_participant = submission_form.participant.data
                new_location = submission_form.location.data
                new_incident_description = submission_form.description.data
                new_incident_status = submission_form.status.data

                if new_incident_description != submission.incident_description:
                    changed = True
                    update_params['incident_description'] = new_incident_description
                if new_incident_status != submission.incident_status:
                    changed = True
                    update_params['incident_status'] = new_incident_status
                if new_location != submission.location:
                    changed = True
                    update_params['location_id'] = new_location.id
                if new_participant != submission.participant:
                    if new_participant:
                        changed = True
                        update_params['participant_id'] = new_participant.id

                update_params['data'] = data

                if changed:
                    services.submissions.find(id=submission_id).update(
                        update_params, synchronize_session=False)
                    db.session.commit()
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
            if master_submission:
                master_form = edit_form_class(
                    request.form,
                    prefix=str(master_submission.id)
                )
            else:
                master_form = None

            submission_form = edit_form_class(
                request.form,
                obj=submission,
                prefix=str(submission.id)
            )

            if sibling_submissions:
                sibling_forms = [
                    edit_form_class(
                        obj=sibling,
                        prefix=str(sibling.id))
                    for sibling in sibling_submissions
                ]
            else:
                sibling_forms = []

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
                    form_fields = master_form.data.keys()
                    data_fields = set(form_fields).intersection(
                        questionnaire_form.tags)
                    changed = False
                    data = master_submission.data.copy()
                    update_params = {}
                    overridden_fields = master_submission.overridden_fields[:] \
                        if master_submission.overridden_fields else []

                    new_verification_status = master_form.data.get('verification_status')
                    new_quarantine_status = master_form.data.get('quarantine_status')

                    if new_quarantine_status in get_valid_values(Submission.QUARANTINE_STATUSES):
                        if master_submission.quarantine_status != new_quarantine_status:
                            changed = True
                        update_params['quarantine_status'] = new_quarantine_status
                    if new_verification_status in get_valid_values(Submission.VERIFICATION_STATUSES):
                        if master_submission.verification_status != new_verification_status:
                            changed = True
                        update_params['verification_status'] = new_verification_status

                    for form_field in data_fields:

                        if data.get(form_field, None) != master_form.data.get(
                                form_field):
                            if (
                                not master_form.data.get(form_field) and
                                isinstance(master_form.data.get(
                                    form_field), list)
                            ):
                                data.pop(form_field, None)
                            else:
                                if master_form.data.get(form_field) is not None:
                                    data[form_field] = master_form.data.get(form_field)

                            if (
                                form_field not in
                                ["quarantine_status",
                                    "verification_status"]
                            ):
                                overridden_fields.append(form_field)
                            changed = True
                    if changed:
                        update_params['data'] = data
                        update_params['overridden_fields'] = array(set(
                            overridden_fields))     # remove duplicates

                        services.submissions.find(
                            id=master_submission.id).update(
                                update_params, synchronize_session=False)
                        db.session.commit()

                else:
                    no_error = False

            if selection == 'obs':
                if submission_form.validate():
                    changed = False
                    data = submission.data.copy()
                    update_params = {}
                    form_fields = set(submission_form.data.keys()).intersection(
                        questionnaire_form.tags)

                    new_verification_status = submission_form.data.get('verification_status')
                    new_quarantine_status = submission_form.data.get('quarantine_status')

                    if new_quarantine_status in get_valid_values(Submission.QUARANTINE_STATUSES):
                        if submission.quarantine_status != new_quarantine_status:
                            changed = True
                        update_params['quarantine_status'] = new_quarantine_status
                    if new_verification_status in get_valid_values(Submission.VERIFICATION_STATUSES):
                        if submission.verification_status != new_verification_status:
                            changed = True
                        update_params['verification_status'] = new_verification_status

                    for form_field in form_fields:
                        if data.get(form_field) != \
                                submission_form.data.get(form_field):
                            if (
                                not submission_form.data.get(
                                    form_field) and
                                isinstance(submission_form.data.get(
                                    form_field), list)
                            ):
                                data.pop(form_field, None)
                            else:
                                if submission_form.data.get(form_field) is not None:
                                    data[form_field] = submission_form.data.get(form_field)
                            changed = True
                    if changed:
                        update_params['data'] = data
                        services.submissions.find(id=submission.id).update(
                            update_params)

                        db.session.commit()
                        update_submission_version(submission)
                    # submission is for a checklist form, update
                    # contributor completion rating
                    # update_participant_completion_rating(
                    #     submission.participant)
                else:
                    no_error = False

            if no_error:
                if request.form.get('next'):
                    return redirect(request.form.get('next'))
                else:
                    return redirect(url_for(
                        'submissions.submission_list',
                        form_id=str(questionnaire_form.id)
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
    submission = services.submissions.fget_or_404(
        id=request.form.get('submission'))
    comment = request.form.get('comment')

    # TODO: fix this hack
    saved_comment = services.submission_comments.new(
        submission=submission,
        user=current_user._get_current_object(),
        comment=comment,
        submit_date=utils.current_timestamp(),
        deployment_id=submission.deployment_id
    )

    saved_comment.save()

    return jsonify(
        comment=saved_comment.comment,
        date=mkunixtimestamp(saved_comment.submit_date),
        user=saved_comment.user.email
    )


def _incident_csv(form_id, location_type_id, location_id=None):
    """Given an incident form id, a location type id, and optionally
    a location id, return a CSV file of the number of incidents of each
    type (form field tag) that has occurred, either for the entire
    deployment or under the given location for each location of the
    specified location type. Only submissions sent in by participants
    are used for generating the data.

    Sample output would be:

    LOC | A | B | ... | Z | TOT
    NY  | 2 | 0 | ... | 5 |  7

    `param form_id`: a `class`Form id
    `param location_type_id`: a `class`LocationType id
    `param location_id`: an optional `class`Location id. if given, only
    submissions under that location will be queried.

    `returns`: a string of bytes (str) containing the CSV data.
    """
    event = get_event()
    form = services.forms.fget_or_404(id=form_id, form_type='INCIDENT')
    location_type = services.location_types.objects.fget_or_404(
        id=location_type_id)

    submission_query = services.submissions.find(
        submission_type='O', form=form, event=event)

    if location_id:
        location_query = models.Location.query.with_entities(
            models.Location.id
        ).join(
            models.LocationPath,
            models.Location.id == models.LocationPath.descendant_id
        ).filter(models.LocationPath.ancestor_id == location_id)

        submission_query = submission_query.filter(
                models.Submission.location_id.in_(location_query))

    tags = form.tags
    submission_query = submission_query.filter(
        models.Submission.created <= event.end,
        models.Submission.created >= event.start)

    df = make_submission_dataframe(submission_query, form)
    ds = Dataset()
    ds.headers = ['LOC'] + tags + ['TOT']

    for summary in incidents_csv(df, location_type.name, tags):
        ds.append([summary.get(heading) for heading in ds.headers])

    return codecs.BOM_UTF8.decode(encoding='utf-8') + ds.csv


@route(bp, '/incidents/form/<form_id>/locationtype/<location_type_id>/incidents.csv')
@login_required
def incidents_csv_dl(form_id, location_type_id):
    response = make_response(
        _incident_csv(form_id, location_type_id))
    response.headers['Content-Type'] = 'text/csv'

    return response


@route(bp, '/incidents/form/<form_id>/locationtype/<location_type_id>/location/<location_id>/incidents.csv')
@login_required
def incidents_csv_with_location_dl(form_id, location_type_id, location_id):
    response = make_response(
        _incident_csv(form_id, location_type_id, location_id))
    response.headers['Content-Type'] = 'text/csv'

    return response


@route(bp, '/submissions/<submission_id>/version/<version_id>')
@login_required
def submission_version(submission_id, version_id):
    event = g.event
    submission = services.submissions.fget_or_404(
        id=submission_id, event_id=event.id)
    version = services.submission_versions.fget_or_404(
        id=version_id, submission_id=submission_id)
    form = submission.form
    form_data = MultiDict(version.data)
    page_title = _('View submission')
    template_name = 'frontend/submission_history.html'

    diff = DictDiffer(submission.data, form_data)

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
        form_type='CHECKLIST', quality_checks_enabled=True))
@permissions.view_quality_assurance.require(403)
@login_required
def quality_assurance_dashboard(form_id):
    form = services.forms.fget_or_404(id=form_id, form_type='CHECKLIST')
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
    check_data = _qa_counts(query_filterset.qs, form)

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
        form_type='CHECKLIST', quality_checks_enabled=True))
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


def update_submission_version(submission):
    # save actual version data
    data_fields = submission.form.tags
    version_data = {
        k: submission.data.get(k)
        for k in data_fields if k in submission.data}

    if submission.form.form_type == 'INCIDENT':
        version_data['status'] = submission.incident_status.code
        version_data['description'] = submission.incident_description

    # get previous version
    previous = services.submission_versions.find(
        submission=submission).order_by(
            models.SubmissionVersion.timestamp.desc()).first()

    if previous:
        diff = DictDiffer(version_data, previous.data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

    # save user email as identity
    channel = 'WEB'
    user = current_user._get_current_object()
    identity = user.email if not user.is_anonymous else 'unknown'

    services.submission_versions.create(
        submission_id=submission.id,
        data=version_data,
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity,
        deployment_id=submission.deployment_id
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
