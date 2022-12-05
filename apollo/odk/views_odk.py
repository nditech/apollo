# -*- coding: utf-8 -*-
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, g, make_response, render_template, request
from flask_babelex import lazy_gettext as _
from flask_httpauth import HTTPDigestAuth
from lxml import etree
import pytz
from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound

from apollo import csrf, models, services, settings
from apollo.core import db
from apollo.formsframework.forms import filter_participants, find_active_forms
from apollo.frontend import route
from apollo.frontend.helpers import DictDiffer
from apollo.odk import utils
from apollo.services import messages
from apollo.utils import current_timestamp

DEFAULT_CONTENT_TYPE = 'text/xml; charset=utf-8'
HTTP_OPEN_ROSA_VERSION_HEADER = 'HTTP_X_OPENROSA_VERSION'
OPEN_ROSA_VERSION = '1.0'
OPEN_ROSA_VERSION_HEADER = 'X-OpenRosa-Version'

NSMAP = {
    'orx': 'http://openrosa.org/xforms',
}


def make_open_rosa_headers():
    return {
        OPEN_ROSA_VERSION_HEADER: OPEN_ROSA_VERSION,
        'Date': pytz.utc.localize(datetime.utcnow()).strftime(
            '%a, %d %b %Y %H:%M:%S %Z'),
        'X-OpenRosa-Accept-Content-Length': settings.MAX_CONTENT_LENGTH
    }


def open_rosa_default_response(**kwargs):
    content = '''<?xml version='1.0' encoding='UTF-8'?>
<OpenRosaResponse xmlns='http://openrosa.org/http/response'>
<message>{}</message>
</OpenRosaResponse>'''.format(kwargs.get('content', ''))
    response = make_response(content, kwargs.get('status_code', 201))

    response.headers.extend(make_open_rosa_headers())

    return response


bp = Blueprint('xforms', __name__, template_folder='templates')

participant_auth = HTTPDigestAuth()


@participant_auth.verify_opaque
def verify_opaque(opaque):
    return True


@participant_auth.verify_nonce
def verify_nonce(nonce):
    return True


@participant_auth.get_password
def get_pw(participant_id):
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)
    participant = current_events.join(
        models.Participant,
        models.Participant.participant_set_id == models.Event.participant_set_id    # noqa
    ).with_entities(
        models.Participant
    ).filter(
        models.Participant.participant_id == participant_id
    ).first()
    return participant.password if participant else None


@route(bp, '/xforms/formList')
def get_form_download_list():
    forms = find_active_forms().order_by('form_type')
    template_name = 'frontend/xformslist.xml'

    response = make_response(render_template(template_name, forms=forms))
    response.headers['Content-Type'] = DEFAULT_CONTENT_TYPE
    response.headers.extend(make_open_rosa_headers())
    return response


@route(bp, '/xforms/xformsManifest/<form_id>')
def get_form_manifest(form_id):
    # not using the parameter since none of the forms uses
    # external files
    template_name = 'frontend/xformsManifest.xml'
    response = make_response(render_template(template_name))
    response.headers['Content-Type'] = DEFAULT_CONTENT_TYPE
    response.headers.extend(make_open_rosa_headers())
    return response


@route(bp, '/xforms/forms/<form_id>/form.xml')
def get_form(form_id):
    form = services.forms.fget_or_404(id=form_id)
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

    current_events = services.events.overlapping_events(
        getattr(g, 'event', services.events.default()))

    # only for ODK Collect
    source_file = request.files.get('xml_submission_file')
    try:
        parser = etree.XMLParser(resolve_entities=False)
        document = etree.parse(source_file, parser)

        form_id = document.xpath('//data/form_id')[0].text
        form = models.Form.query.filter_by(id=form_id).one()

        participant = filter_participants(form, participant_auth.username())
        if not form:
            return open_rosa_default_response(
                content=_('Invalid Form Specified'), status_code=404)

        if not participant:
            return open_rosa_default_response(
                content=_('Invalid Participant ID'), status_code=404)
    except (IndexError, etree.LxmlError, NoResultFound):
        return open_rosa_default_response(status_code=400)

    submission = None

    if form.form_type == 'CHECKLIST':
        submission = models.Submission.query.filter_by(
            participant=participant,
            form=form, submission_type='O',
            deployment=form.deployment).first()
    elif form.form_type == 'SURVEY':
        try:
            form_serial = document.xpath('//data/form_serial')[0].text
            submission = models.Submission.query.filter_by(
                participant=participant,
                serial_no=form_serial,
                form=form, submission_type='O',
                deployment=form.deployment).first()
        except IndexError:
            submission = None
    else:
        event = current_events.join(models.Event.forms).filter(
            models.Event.forms.contains(form),
            models.Event.participant_set_id == participant.participant_set_id
        ).order_by(models.Event.end.desc()).first()
        submission = models.Submission(
            participant=participant,
            deployment=participant.participant_set.deployment,
            event=event,
            form=form,
            location=participant.location,
            submission_type='O',
        )
        submission.save()

    if not submission:
        # no existing submission for that form and participant
        return open_rosa_default_response(
            content=_('Checklist Not Found'), status_code=404)

    form_modified = False
    submitted_version_id = None

    try:
        submitted_version_id = document.xpath(
            '//data/@orx:version', namespaces=NSMAP)[0]
    except (IndexError, etree.LxmlError):
        pass

    if form.version_identifier != submitted_version_id:
        form_modified = True

    tag_finder = etree.XPath('//data/*[local-name() = $tag]')
    data = {}
    attachments = []
    deleted_attachments = []
    geopoint_lat = None
    geopoint_lon = None
    for tag in form.tags:
        field = form.get_field_by_tag(tag)
        field_type = field.get('type')
        try:
            element = tag_finder(document, tag=tag)[0]
        except IndexError:
            # normally shouldn't happen, but the form might have been
            # modified
            form_modified = True
            continue

        if element.text:
            if field_type in ('comment', 'string'):
                data[tag] = element.text
            elif field_type == 'multiselect':
                try:
                    data[tag] = sorted(int(i) for i in element.text.split())
                except ValueError:
                    continue
            elif field_type == 'image':
                original_field_data = submission.data.get(tag)
                file_wrapper = request.files.get(element.text)
                identifier = uuid4()

                if file_wrapper.mimetype.startswith('image/'):
                    if original_field_data is not None:
                        original_attachment = \
                            models.SubmissionImageAttachment.query.filter_by(   # noqa
                                uuid=original_field_data).first()
                        if original_attachment:
                            deleted_attachments.append(original_attachment)
                    if file_wrapper and file_wrapper.filename != '':
                        data[tag] = identifier.hex
                        attachments.append(
                            models.SubmissionImageAttachment(
                                photo=file_wrapper, submission=submission,
                                uuid=identifier)
                        )
            else:
                try:
                    data[tag] = int(element.text)
                except ValueError:
                    continue
    try:
        element = tag_finder(document, tag='location')[0]
        geodata = element.text.split() if element.text else []

        try:
            geopoint_lat = float(geodata[0])
            geopoint_lon = float(geodata[1])
        except (IndexError, ValueError):
            pass
    except IndexError:
        pass

    submission.data = data
    submission.participant_updated = current_timestamp()
    if geopoint_lat is not None and geopoint_lon is not None:
        submission.geom = 'SRID=4326; POINT({longitude:f} {latitude:f})'.format(    # noqa
            longitude=geopoint_lon, latitude=geopoint_lat)

    # set the 'voting_timestamp' extra data attribute to the current timestamp
    # only if a voting share was updated and it has not been previously set
    if (
        any(vs in data.keys() for vs in submission.form.vote_shares)
        and not (submission.extra_data or {}).get('voting_timestamp')
    ):
        extra_data = submission.extra_data or {}
        extra_data['voting_timestamp'] = current_timestamp().isoformat()
        submission.extra_data = extra_data

    db.session.add(submission)
    db.session.add_all(attachments)
    for attachment in deleted_attachments:
        db.session.delete(attachment)
    db.session.commit()
    models.Submission.update_related(submission, data)
    update_submission_version(submission)

    message_text = utils.make_message_text(form, participant, data)
    sender = participant.primary_phone or participant.participant_id
    message = messages.log_message(
        event=submission.event, direction='IN', text=message_text,
        sender=sender, message_type='ODK')
    message.participant = participant
    message.submission_id = submission.id
    message.save()

    if form_modified:
        return open_rosa_default_response(
            content=_(
                'Your submission was received, '
                'but you sent it using an outdated form. Please download a '
                'new copy and resend. Thank you.'), status_code=202)
    return open_rosa_default_response(status_code=201)


def update_submission_version(submission):
    # save actual version data
    data_fields = submission.form.tags
    version_data = {
        k: submission.data.get(k)
        for k in data_fields if k in submission.data}

    if submission.form.form_type == 'INCIDENT':
        if submission.incident_status:
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

    # use participant ID as identity
    channel = 'ODK'
    identity = participant_auth.username()

    services.submission_versions.create(
        submission=submission,
        data=version_data,
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity,
        deployment_id=submission.deployment_id
    )


@route(bp, '/xforms/setup')
def collect_qr_setup():
    participant_id = request.args.get('participant')
    participant = models.Participant.query.filter_by(id=participant_id).first()
    response = make_response(utils.generate_config_qr_code(participant))
    response.mimetype = 'image/png'

    return response
