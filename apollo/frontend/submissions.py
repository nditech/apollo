# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import (
    Blueprint, jsonify, make_response, render_template, request
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security.core import current_user
from flask.ext.menu import register_menu
from tablib import Dataset
from ..analyses.incidents import incidents_csv
from ..models import Location
from ..services import (
    forms, location_types, submissions, submission_comments
)
from . import route
from .filters import generate_submission_filter
from .helpers import (
    displayable_location_types, get_event, get_form_list_menu)
from functools import partial

PAGE_SIZE = 25
bp = Blueprint('submissions', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/submissions/<form_id>', methods=['GET', 'POST'])
@register_menu(bp, 'forms.checklists', _('Checklists'),
               dynamic_list_constructor=partial(get_form_list_menu,
                                                form_type='CHECKLIST'))
@register_menu(bp, 'forms.incidents', _('Critical Incidents'),
               dynamic_list_constructor=partial(get_form_list_menu,
                                                form_type='INCIDENT'))
def submission_list(form_id):
    form = forms.get_or_404(pk=form_id)
    filter_class = generate_submission_filter(form)
    page_title = form.name
    template_name = 'frontend/nu_submission_list.html'

    data = request.args.copy()
    data.add('form_id', form.pk)
    page = int(data.pop('page', 1))

    loc_types = displayable_location_types()

    queryset = submissions.find(
        contributor__ne=None,
        form=form
    )
    query_filterset = filter_class(queryset, request.args)
    filter_form = query_filterset.form

    if form.form_type == 'CHECKLIST':
        form_fields = []
    else:
        form_fields = [field for group in form.groups for field in group.fields]

    return render_template(
        template_name,
        args=data,
        filter_form=filter_form,
        form=form,
        form_fields=form_fields,
        location_types=loc_types,
        page_title=page_title,
        pager=query_filterset.qs.paginate(page=page, per_page=PAGE_SIZE)
    )


@route(bp, '/comments', methods=['POST'])
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
def incidents_csv_dl(form_pk, location_type_pk):
    response = make_response(
        _incident_csv(form_pk, location_type_pk))
    response.headers['Content-Type'] = 'text/csv'

    return response


@route(bp, '/incidents/form/<form_pk>/locationtype/<location_type_pk>/location/<location_pk>/incidents.csv')
def incidents_csv_with_location_dl(form_pk, location_type_pk, location_pk):
    response = make_response(
        _incident_csv(form_pk, location_type_pk, location_pk))
    response.headers['Content-Type'] = 'text/csv'

    return response
