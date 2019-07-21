# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
import logging
from operator import itemgetter
import re

from flask_babelex import lazy_gettext as _
from lxml import etree
from lxml.builder import E, ElementMaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType
from slugify import slugify_unicode
from unidecode import unidecode

from apollo.core import db
from apollo.dal.models import Resource

NSMAP = {
    None: 'http://www.w3.org/2002/xforms',
    'h': 'http://www.w3.org/1999/xhtml',
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'jr': 'http://openrosa.org/javarosa',
    'odk': 'http://www.opendatakit.org/xforms',
    'orx': 'http://openrosa.org/xforms',
}

HTML_E = ElementMaker(namespace=NSMAP['h'], nsmap=NSMAP)
SCHEMA_E = ElementMaker(namespace=NSMAP['xsd'], nsmap=NSMAP)
ROSA_E = ElementMaker(namespace=NSMAP['jr'], nsmap=NSMAP)


FIELD_TYPES = (
    'boolean', 'comment', 'integer', 'select', 'multiselect',
    'category', 'string', 'location'
)

logger = logging.getLogger(__name__)

gt_constraint_regex = re.compile(r'(?:.*\.\s*\>={0,1}\s*)(\d+)')
lt_constraint_regex = re.compile(r'(?:.*\.\s*\<={0,1}\s*)(\d+)')


def _make_version_identifer():
    return datetime.utcnow().strftime('%Y%m%d%H%M%S%f')


events_forms = db.Table(
    'events_forms',
    db.Column(
        'event_id', db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'),
        primary_key=True),
    db.Column(
        'form_id', db.Integer, db.ForeignKey('form.id', ondelete='CASCADE'),
        primary_key=True)
)


class Form(Resource):
    FORM_TYPES = (
        ('CHECKLIST', _('Checklist Form')),
        ('INCIDENT', _('Incident Form'))
    )

    __mapper_args__ = {'polymorphic_identity': 'form'}
    __tablename__ = 'form'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    prefix = db.Column(db.String, nullable=False)
    form_type = db.Column(ChoiceType(FORM_TYPES), nullable=False)
    require_exclamation = db.Column(db.Boolean, default=True)
    track_data_conflicts = db.Column(db.Boolean, default=True, nullable=False)
    data = db.Column(JSONB)
    version_identifier = db.Column(
        db.String, default=_make_version_identifer,
        onupdate=_make_version_identifer)
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'))
    quality_checks = db.Column(JSONB)
    party_mappings = db.Column(JSONB)
    calculate_moe = db.Column(db.Boolean)
    accredited_voters_tag = db.Column(db.String)
    quality_checks_enabled = db.Column(db.Boolean, default=False)
    invalid_votes_tag = db.Column(db.String)
    registered_voters_tag = db.Column(db.String)
    blank_votes_tag = db.Column(db.String)

    events = db.relationship('Event', backref='forms', secondary=events_forms)

    def __str__(self):
        return str(_('Form - %(name)s', name=self.name))

    def _populate_field_cache(self):
        if self.data:
            self._field_cache = {
                f['tag']: f for g in self.data.get('groups', [])
                for f in g.get('fields', [])
            }
        else:
            self._field_cache = {}

    def _populate_group_cache(self):
        if self.data:
            self._group_cache = {
                g['name']: g for g in self.data.get('groups', [])
            }
        else:
            self._group_cache = {}

    def get_form_type_display(self):
        d = dict(Form.FORM_TYPES)
        return d[self.form_type]

    @property
    def tags(self):
        if not hasattr(self, '_field_cache'):
            self._populate_field_cache()

        return sorted(self._field_cache.keys())

    @property
    def vote_tags(self):
        if not hasattr(self, '_field_cache'):
            self._populate_field_cache()

        return sorted([
            key for key in self._field_cache.keys()
            if self._field_cache[key]['analysis_type'] == 'RESULT'])

    def get_field_by_tag(self, tag):
        if not hasattr(self, '_field_cache'):
            self._populate_field_cache()

        return self._field_cache.get(tag)

    def get_group_tags(self, group_name):
        if not hasattr(self, '_group_cache'):
            self._populate_group_cache()

        grp = self._group_cache.get(group_name)
        tags = []

        if grp and grp.get('fields'):
            for f in grp.get('fields'):
                if f and f.get('tag'):
                    tags.append(f.get('tag'))

        return tags

    def to_xml(self):
        root = HTML_E.html()
        head = HTML_E.head(HTML_E.title(self.name))
        data = E.data(id=self.uuid.hex)
        model = E.model(E.instance(data))

        body = HTML_E.body()

        model.append(E.bind(nodeset='/data/form_id', readonly='true()'))
        model.append(E.bind(nodeset='/data/version_id', readonly='true()'))
        form_id = etree.Element('form_id')
        form_id.text = str(self.id)
        data.append(form_id)

        data.append(E.device_id())
        data.append(E.subscriber_id())
        data.append(E.phone_number())
        data.attrib['{{{}}}version'.format(NSMAP['orx'])] = \
            self.version_identifier

        device_id_bind = E.bind(nodeset='/data/device_id')
        device_id_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = \
            'property'
        device_id_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = \
            'deviceid'

        subscriber_id_bind = E.bind(nodeset='/data/subscriber_id')
        subscriber_id_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = 'property'  # noqa
        subscriber_id_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = 'subscriberid'  # noqa

        phone_number_bind = E.bind(nodeset='/data/phone_number')
        phone_number_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = 'property'  # noqa
        phone_number_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = 'phonenumber'  # noqa

        model.append(device_id_bind)
        model.append(subscriber_id_bind)
        model.append(phone_number_bind)

        for group in self.data['groups']:
            grp_element = E.group(E.label(group['name']))
            for field in group['fields']:
                data.append(etree.Element(field['tag']))
                path = '/data/{}'.format(field['tag'])

                field_type = field.get('type')
                if field_type == 'boolean':
                    field_element = E.select1(
                            E.label(field['description']),
                            E.item(E.label('True'), E.value('1')),
                            E.item(E.label('False'), E.value('0')),
                            ref=field['tag']
                        )
                    model.append(E.bind(nodeset=path, type='select1'))
                elif field_type == 'location':
                    field_element = E.input(
                        E.label(field['description']), ref=field['tag'])
                    model.append(E.bind(nodeset=path, type='geopoint'))
                elif field_type in ('comment', 'string'):
                    field_element = E.input(
                            E.label(field['description']),
                            ref=field['tag']
                        )
                    model.append(E.bind(nodeset=path, type='string'))
                elif field_type == 'integer':
                    field_element = E.input(
                        E.label(field['description']),
                        ref=field['tag']
                    )
                    model.append(E.bind(
                        nodeset=path, type='integer',
                        constraint='. >= {} and . <= {}'.format(
                            field.get('min', 0),
                            field.get('max', 9999)
                        )))
                elif field_type in ('select', 'multiselect', 'category'):
                    sorted_options = sorted(field.get('options').items(),
                                            key=itemgetter(1))
                    if field_type == 'select' or field_type == 'category':
                        element_factory = E.select1
                        model.append(E.bind(nodeset=path, type='select1'))
                    else:
                        element_factory = E.select
                        model.append(E.bind(nodeset=path, type='select'))

                    field_element = element_factory(
                        E.label(field['description']),
                        ref=field['tag']
                    )
                    for key, value in sorted_options:
                        field_element.append(
                            E.item(E.label(key), E.value(str(value)))
                        )
                else:
                    continue

                grp_element.append(field_element)
            body.append(grp_element)

        # hard coding a location question here until the form builder
        # gets updated. please remove once the form builder supports
        # locations
        description = str(_('Location'))
        path = '/data/location'
        data.append(etree.Element('location'))
        model.append(E.bind(nodeset=path, type='geopoint'))

        grp_element = E.group(E.label(description))
        field_element = E.input(E.label(description), ref='location')
        grp_element.append(field_element)
        body.append(grp_element)

        head.append(model)
        root.append(head)
        root.append(body)

        return root

    def odk_hash(self):
        xform_data = etree.tostring(
            self.to_xml(), encoding='UTF-8', xml_declaration=True)
        hash_engine = hashlib.md5()
        hash_engine.update(xform_data)
        return f'md5: {hash_engine.hexdigest()}'


class FormBuilderSerializer(object):
    @classmethod
    def serialize_field(cls, field):
        data = {
            'label': field['tag'],
            'description': field['description'],
            'analysis': field.get('analysis_type')
        }

        field_type = field.get('type')
        if field_type in ('comment', 'string'):
            data['component'] = 'textarea'
        elif field_type == 'boolean':
            data['component'] = 'textInput'
            data['required'] = True
            data['min'] = field.get('min', 0)
            data['max'] = field.get('max', 1)
        elif field_type == 'integer':
            data['component'] = 'textInput'
            data['min'] = field.get('min', 0)
            data['max'] = field.get('max', 9999)
        elif field_type in ('select', 'multiselect', 'category'):
            sorted_options = sorted(field['options'].items(),
                                    key=itemgetter(1))
            data['options'] = [opt[0] for opt in sorted_options]
            if field_type == 'multiselect':
                data['component'] = 'checkbox'
            else:
                data['component'] = 'radio'
        else:
            return {}

        return data

    @classmethod
    def serialize_group(cls, group):
        field_data = []

        field_data.append({
            'label': group['name'],
            'component': 'group'
        })

        field_data.extend([cls.serialize_field(f) for f in group['fields']])

        return field_data

    @classmethod
    def serialize(cls, form):
        group_data = []
        if form.data:
            for group in form.data['groups']:
                group_data.extend(cls.serialize_group(group))
        data = {'fields': group_data}
        return data

    @classmethod
    def deserialize(cls, form, data):
        groups = []
        current_group = None

        # verify that first field is always a group
        if len(data['fields']) > 0:
            if data['fields'][0]['component'] != 'group':
                # no group was created, create a default
                group = {
                    'name': str(_('SMS 1')),
                    'slug': unidecode(slugify_unicode(str(_('SMS 1')))),
                    'fields': []
                }
                groups.append(group)
                current_group = group

        for f in data['fields']:
            if f['component'] == 'group':
                group = {
                    'name': f['label'],
                    'slug': unidecode(slugify_unicode(f['label'])),
                    'fields': []
                }
                current_group = group
                groups.append(group)
                continue

            field = {
                'tag': f['label'],
                'description': f['description']
            }

            if f['analysis']:
                field['analysis_type'] = f['analysis']
            else:
                field['analysis_type'] = 'N/A'

            # TODO: this formbuilder doesn't yet support
            # string fields
            if f['component'] == 'textarea':
                field['type'] = 'comment'
                field['analysis_type'] = 'N/A'
            elif f['component'] == 'textInput':
                if f['required']:
                    field['type'] = 'boolean'
                    field['min'] = 0
                    field['max'] = 1
                else:
                    field['type'] = 'integer'
                    try:
                        min_limit = int(f.get('min', 0))
                    except ValueError:
                        min_limit = 0

                    try:
                        max_limit = int(f.get('max', 9999))
                    except ValueError:
                        max_limit = 9999

                    field['min'] = min_limit
                    field['max'] = max_limit
            else:
                field['options'] = {
                    k: v for v, k in enumerate(f['options'], 1)}
                if f['component'] == 'checkbox':
                    field['type'] = 'multiselect'
                else:
                    field['type'] = 'select'

            current_group['fields'].append(field)

            # invalidate the form cache
            if hasattr(form, '_field_cache'):
                delattr(form, '_field_cache')
            if hasattr(form, '_group_cache'):
                delattr(form, '_group_cache')
            if hasattr(form, '_schema_cache'):
                delattr(form, '_schema_cache')

        form.data = {'groups': groups}
        form.save()
