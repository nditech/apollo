# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import Blueprint, g, jsonify, render_template, request, session
from flask.ext.security.core import current_user
from ..models import Form, Location, Participant, Sample, Submission
from ..services import submissions, submission_comments
from . import route
from .forms import generate_submission_filter_form
from .helpers import _get_event

PAGE_SIZE = 25
core = Blueprint('core', __name__, template_folder='templates',
                 static_folder='static', static_url_path='/core/static')


@route(core, '/submissions/<form_id>', methods=['GET', 'POST'])
def submission_list(form_id):
    event = _get_event(session)
    deployment = g.get('deployment')
    form = Form.objects.get_or_404(deployment=deployment, pk=form_id)
    template_name = 'core/submission_list.html'

    queryset = Submission.objects(
        contributor__ne=None,
        created__lte=event.end_date,
        created__gte=event.start_date,
        deployment=deployment,
        form=form
    )

    if request.method == 'GET':
        filter_form = generate_submission_filter_form(form, event)
        return render_template(
            template_name,
            filter_form=filter_form,
            queryset=queryset
        )
        print queryset._query
    else:
        filter_form = generate_submission_filter_form(
            form, event, request.form)

        # process filter form
        for field in filter_form:
            if field.errors:
                continue

            # filter on groups
            if field.name.startswith('group_') and field.data:
                slug = field.name.split('_', 1)[1]
                try:
                    group = [grp.name for grp in form.groups
                             if grp.slug == slug][0]
                except IndexError:
                    continue
                if field.data == '0':
                    continue
                elif field.data == '1':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Partial'})
                elif field.data == '2':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Missing'})
                elif field.data == '3':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Complete'})
            else:
                # filter 'regular' fields
                if field.name == 'participant_id' and field.data:
                    # participant ID
                    participant = Participant.objects.get_or_404(
                        participant_id=field.data)
                    queryset = queryset(contributor=participant)
                elif field.name == 'location' and field.data:
                    # location
                    location = Location.objects.get_or_404(pk=field.data)
                    queryset = queryset.filter_in(location)
                elif field.name == 'sample' and field.data:
                    # sample
                    sample = Sample.objects.get_or_404(pk=field.data)
                    locations = Location.objects(samples=sample)
                    queryset = queryset(location__in=locations)

        print queryset._query
        return render_template(
            template_name,
            filter_form=filter_form,
            queryset=queryset
        )


@route(core, '/comments', methods=['POST'])
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
