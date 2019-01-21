# -*- coding: utf-8 -*-
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
from xlwt import Workbook

from apollo.core import db
from apollo.dal.models import BaseModel, Resource

NSMAP = {
    None: 'http://www.w3.org/2002/xforms',
    'h': 'http://www.w3.org/1999/xhtml',
    'ev': 'http://www.w3.org/2001/xml-events',
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'jr': 'http://openrosa.org/javarosa'
}

HTML_E = ElementMaker(namespace=NSMAP['h'], nsmap=NSMAP)
EVT_E = ElementMaker(namespace=NSMAP['ev'], nsmap=NSMAP)
SCHEMA_E = ElementMaker(namespace=NSMAP['xsd'], nsmap=NSMAP)
ROSA_E = ElementMaker(namespace=NSMAP['jr'], nsmap=NSMAP)

FIELD_TYPES = (
    'boolean', 'comment', 'integer', 'select', 'multiselect',
    'category', 'string'
)

logger = logging.getLogger(__name__)

gt_constraint_regex = re.compile('(?:.*\.\s*\>={0,1}\s*)(\d+)')
lt_constraint_regex = re.compile('(?:.*\.\s*\<={0,1}\s*)(\d+)')


class FormSet(BaseModel):
    __tablename__ = 'form_set'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    deployment = db.relationship(
        'Deployment', backref=db.backref('form_sets', cascade='all, delete',
                                         passive_deletes=True))

    def __str__(self):
        return self.name or ''


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
    version_identifier = db.Column(db.String)
    form_set_id = db.Column(
        db.Integer, db.ForeignKey('form_set.id'), nullable=False)
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

    form_set = db.relationship(
        'FormSet', backref=db.backref('forms', lazy='dynamic'),
        cascade='all, delete')

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

    def to_excel(self):
        book = Workbook()
        survey_sheet = book.add_sheet('survey')
        choices_sheet = book.add_sheet('choices')
        analysis_sheet = book.add_sheet('analysis')
        metadata_sheet = book.add_sheet('metadata')

        survey_header = ['type', 'name', 'label', 'constraints']
        choices_header = ['list name', 'name', 'label']
        analysis_header = ['name', 'analysis']
        metadata_header = ['name', 'prefix', 'form_type',
                           'require_exclamation', 'calculate_moe',
                           'accredited_voters_tag', 'invalid_votes_tag',
                           'registered_voters_tag', 'blank_votes_tag',
                           'quality_checks_enabled']

        # HEADERS
        for col, value in enumerate(survey_header):
            survey_sheet.write(0, col, value)

        for col, value in enumerate(choices_header):
            choices_sheet.write(0, col, value)

        for col, value in enumerate(analysis_header):
            analysis_sheet.write(0, col, value)

        for col, value in enumerate(metadata_header):
            metadata_sheet.write(0, col, value)

        # fill out form metadata
        metadata_sheet.write(1, 0, self.name)
        metadata_sheet.write(1, 1, self.prefix)
        metadata_sheet.write(1, 2, self.form_type.code)
        metadata_sheet.write(1, 3, 1 if self.require_exclamation else 0)
        metadata_sheet.write(1, 4, 1 if self.calculate_moe else 0)
        metadata_sheet.write(1, 5, self.accredited_voters_tag)
        metadata_sheet.write(1, 6, self.invalid_votes_tag)
        metadata_sheet.write(1, 7, self.registered_voters_tag)
        metadata_sheet.write(1, 8, self.blank_votes_tag)
        metadata_sheet.write(1, 9, 1 if self.quality_checks_enabled else 0)

        current_survey_row = 1
        current_choices_row = 1
        current_analysis_row = 1
        groups = self.data.get('groups')
        if groups and isinstance(groups, list):
            boolean_written = False
            current_group = None
            for group in groups:
                if not group:
                    continue

                if current_group:
                    current_group = group
                    survey_sheet.write(current_survey_row, 0, 'end group')
                    current_survey_row += 1
                survey_sheet.write(current_survey_row, 0, 'begin group')
                survey_sheet.write(
                    current_survey_row, 1, slugify_unicode(group['name']))
                survey_sheet.write(current_survey_row, 2, group['name'])
                current_survey_row += 1
                current_group = group

                fields = group.get('fields')
                if fields and isinstance(fields, list):
                    for field in fields:
                        # output the type
                        if field['type'] == 'integer':
                            survey_sheet.write(
                                current_survey_row, 0, 'integer')
                            survey_sheet.write(
                                current_survey_row, 3,
                                '. >= {} and . <= {}'.format(
                                    field.get('min', 0),
                                    field.get('max', 9999)))
                        elif field['type'] == 'boolean':
                            survey_sheet.write(
                                current_survey_row, 0, 'select_one boolean')

                            # write out boolean choices if they haven't been
                            # written before
                            if not boolean_written:
                                choices_sheet.write(
                                    current_choices_row, 0, 'boolean')
                                choices_sheet.write(current_choices_row, 1, 0)
                                choices_sheet.write(
                                    current_choices_row, 2, 'False')
                                current_choices_row += 1
                                choices_sheet.write(
                                    current_choices_row, 0, 'boolean')
                                choices_sheet.write(current_choices_row, 1, 1)
                                choices_sheet.write(
                                    current_choices_row, 2, 'True')
                                boolean_written = True

                        elif field['type'] in ('comment', 'string'):
                            survey_sheet.write(current_survey_row, 0, 'text')
                        else:
                            # for questions with choices, write them to the
                            # choices sheet
                            option_list_name = '{}_options'.format(
                                field['tag'])
                            options = field.get('options')
                            for description, value in options.items():
                                choices_sheet.write(
                                    current_choices_row, 0, option_list_name)
                                choices_sheet.write(
                                    current_choices_row, 1, value)
                                choices_sheet.write(
                                    current_choices_row, 2, description)
                                current_choices_row += 1

                            if field['type'] == 'select':
                                survey_sheet.write(
                                    current_survey_row, 0,
                                    'select_one {}'.format(option_list_name))
                            else:
                                survey_sheet.write(
                                    current_survey_row, 0,
                                    'select_multiple {}'.format(
                                        option_list_name))

                        # output the name and description
                        survey_sheet.write(current_survey_row, 1, field['tag'])
                        survey_sheet.write(
                            current_survey_row, 2, field['description'])
                        current_survey_row += 1

                        # also output the analysis
                        analysis_sheet.write(
                            current_analysis_row, 0, field['tag'])
                        analysis_sheet.write(
                            current_analysis_row, 1, field['analysis_type'])
                        current_analysis_row += 1

            if current_group:
                survey_sheet.write(current_survey_row, 0, 'end group')

        return book

    def to_xml(self):
        root = HTML_E.html()
        head = HTML_E.head(HTML_E.title(self.name))
        data = E.data(id='-1')
        model = E.model(E.instance(data))

        body = HTML_E.body()
        model.append(E.bind(nodeset='/data/form_id', readonly='true()'))
        model.append(E.bind(nodeset='/data/version_id', readonly='true()'))

        form_id = etree.Element('form_id')
        form_id.text = str(self.id)

        version_id = etree.Element('version_id')
        version_id.text = self.version_identifier

        data.append(form_id)
        data.append(version_id)

        data.append(E.device_id())
        data.append(E.subscriber_id())
        data.append(E.phone_number())

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
                elif field_type in ('select', 'multiselect'):
                    sorted_options = sorted(field.get('options').items(),
                                            key=itemgetter(1))
                    if field_type == 'select':
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

        head.append(model)
        root.append(head)
        root.append(body)

        return root


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
        elif field_type in ('select', 'multiselect'):
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

        if len(data['fields']) > 0:
            if data['fields'][0]['component'] != 'group':
                raise ValueError('Fields specified outside of group')

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
