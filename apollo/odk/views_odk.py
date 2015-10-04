# -*- coding: utf-8 -*-
from datetime import datetime
import json

from flask import Blueprint, g, make_response, render_template, request
from flask_httpauth import HTTPDigestAuth
from lxml import etree
from mongoengine import signals
from slugify import slugify

from apollo import services, csrf
from apollo.frontend import route
from apollo.frontend.helpers import DictDiffer

DEFAULT_CONTENT_LENGTH = 1000000
DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'


def make_open_rosa_headers():
    return {
        OPEN_ROSA_VERSION_HEADER: OPEN_ROSA_VERSION,
        'Date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S %Z'),
        'X-OpenRosa-Accept-Content-Length': DEFAULT_CONTENT_LENGTH
    }


def open_rosa_default_response(**kwargs):
    content = '''<?xml version='1.0' encoding='UTF-8'?>
<OpenRosaResponse xmlns='http://openrosa.org/http/response'>
<message nature=''>{}</message>
</OpenRosaResponse>'''.format(kwargs.get('content', ''))
    response = make_response(content, kwargs.get('status_code', 201))

    response.headers.extend(make_open_rosa_headers())

    return response


bp = Blueprint('xforms', __name__, template_folder='templates')

participant_auth = HTTPDigestAuth()


@participant_auth.get_password
def get_pw(participant_id):
    participant = services.participants.get(participant_id=participant_id)
    return participant.password if participant else None


@route(bp, '/xforms/formList')
def get_form_download_list():
    forms = services.forms.find()
    template_name = 'frontend/xformslist.xml'

    response = make_response(render_template(template_name, forms=forms))
    response.headers['Content-Type'] = DEFAULT_CONTENT_TYPE
    response.headers.extend(make_open_rosa_headers())
    return response


@route(bp, '/xforms/xformsManifest/<form_pk>')
def get_form_manifest(form_pk):
    # not using the parameter since none of the forms uses
    # external files
    template_name = 'frontend/xformsManifest.xml'
    response = make_response(render_template(template_name))
    response.headers['Content-Type'] = DEFAULT_CONTENT_TYPE
    response.headers.extend(make_open_rosa_headers())
    return response


@route(bp, '/xforms/forms/<form_pk>/form.xml')
def get_form(form_pk):
    form = services.forms.get_or_404(id=form_pk)
    xform_data = etree.tostring(
        form.to_xml(),
        encoding='UTF-8',
        xml_declaration=True
    )
    response = make_response(xform_data)
    response.headers.extend(make_open_rosa_headers())
    response.headers['Content-Type'] = DEFAULT_CONTENT_TYPE
    response.headers['Content-Disposition'] =\
        'attachment; filename={}.xml'.format(slugify(form.name))

    return response

@csrf.exempt
@route(bp, '/xforms/submission', methods=['HEAD', 'POST'])
@participant_auth.login_required
def submission():
    if request.method == 'HEAD':
        response = open_rosa_default_response(status_code=204)
        return response

    # only for ODK Collect
    source_file = request.files.get('xml_submission_file')
    try:
        parser = etree.XMLParser(resolve_entities=False)
        document = etree.parse(source_file, parser)

        form_pk = document.xpath('//data/form_id')[0].text
        form = services.forms.get(pk=form_pk)

        participant = services.participants.get(participant_id=participant_auth.username())
        if not form or not participant:
            return open_rosa_default_response(status_code=404)
    except (IndexError, etree.LxmlError):
        return open_rosa_default_response(status_code=400)

    submission = services.submissions.find(
        contributor=participant,
        form=form,
        submission_type='O'
    ).order_by('-created').first()

    if not submission:
        submission = services.submissions.new(
            contributor=participant,
            created=datetime.utcnow(),
            deployment=g.deployment,
            event=g.event,
            form=form,
            location=participant.location,
            submission_type='O',
        )

    for tag in form.tags:
        path_spec = '//data/{}'.format(tag)
        element = document.xpath(path_spec)[0]
        if element.text and getattr(submission, tag, None):
            setattr(submission, tag, int(element.text))

    with signals.post_save.connected_to(
        update_submission_version,
        sender=services.submissions.__model__
    ):
        submission.save()

    return open_rosa_default_response(status_code=201)


def update_submission_version(sender, document, **kwargs):
    if sender != services.submissions.__model__:
        return

    # save actual version data
    data_fields = document.form.tags
    if document.form.form_type == 'INCIDENT':
        data_fields.extend(['status', 'witness'])
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

    # use participant ID as identity
    channel = 'WEB'
    identity = participant_auth.username()

    services.submission_versions.create(
        submission=document,
        data=json.dumps(version_data),
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity
    )
