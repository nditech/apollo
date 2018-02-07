# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from lxml import etree
from lxml.builder import E, ElementMaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db2
from apollo.dal.models import Resource

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


class Form(Resource):
    FORM_TYPES = (
        (0, _('Checklist Form')),
        (1, _('Incident Form'))
    )

    __mapper_args__ = {'polymorphic_identity': 'form'}
    __tablename__ = 'form'

    id = db2.Column(
        db2.Integer, db2.Sequence('form_id_seq'), primary_key=True)
    name = db2.Column(db2.String, nullable=False)
    prefix = db2.Column(db2.String)
    form_type = db2.Column(ChoiceType(FORM_TYPES))
    require_exclamation = db2.Column(db2.Boolean, default=True)
    data = db2.Column(JSONB)
    version_identifier = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    form_set_id = db2.Column(db2.Integer, db2.ForeignKey('form_set.id'))
    resource_id = db2.Column(
        db2.Integer, db2.ForeignKey('resource.resource_id'))
    quality_checks = db2.Column(JSONB)
    party_mappings = db2.Column(JSONB)
    calculate_moe = db2.Column(db2.Boolean)
    accreditated_voters_tag = db2.Column(db2.String)
    quality_checks_enabled = db2.Column(db2.Boolean, default=False)
    invalid_votes_tag = db2.Column(db2.String)
    registered_votes_tag = db2.Column(db2.String)
    blank_votes_tag = db2.Column(db2.String)

    deployment = db2.relationship('Deployment', backref='forms')
    form_set = db2.relationship('FormSet', backref='forms')

    def _populate_field_cache(self):
        self._field_cache = {
            f['tag']: f for g in self.data['groups'] for f in g['fields']
        }

    def _populate_group_cache(self):
        self._group_cache = {
            g['name']: g for g in self.data['groups']
        }

    @property
    def tags(self):
        if not hasattr(self, '_field_cache'):
            self._populate_field_cache()

        return sorted(self._field_cache.keys())

    def get_field_by_tag(self, tag):
        if not hasattr(self, '_field_cache'):
            self._populate_field_cache()

        return self._field_cache.get(tag)

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
        data.append(E.phone_number())
        data.append(E.phone_number())

        device_id_bind = E.bind(nodeset='/data/device_id')
        device_id_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = \
            'property'
        device_id_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = \
            'deviceid'

        subscriber_id_bind = E.bind(nodeset='/data/subscriber_id')
        subscriber_id_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = \
            'property'
        subscriber_id_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = \
            'subscriberid'

        phone_number_bind = E.bind(nodeset='/data/phone_number')
        phone_number_bind.attrib['{{{}}}preload'.format(NSMAP['jr'])] = 'property'
        phone_number_bind.attrib['{{{}}}preloadParams'.format(NSMAP['jr'])] = 'phonenumber'

        model.append(device_id_bind)
        model.append(subscriber_id_bind)
        model.append(phone_number_bind)

        for group in self.data['groups']:
            grp_element = E.group(E.label(group['name']))
            for field in group['fields']:
                data.append(etree.Element(field['tag']))
                path = '/data/{}'.format(field['tag'])

                # TODO: construct field data

            body.append(grp_element)

        head.append(model)
        root.append(head)
        root.append(body)

        return root
