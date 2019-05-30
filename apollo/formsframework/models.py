# -*- coding: utf-8 -*-
import hashlib
from operator import itemgetter
from uuid import uuid4
from apollo.core import db
from apollo.deployments.models import Deployment, Event
from apollo.users.models import Role, Need
from flask.ext.babel import lazy_gettext as _
from lxml import etree
from lxml.builder import E, ElementMaker
from slugify import slugify_unicode
from unidecode import unidecode


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


class FormFieldNameField(db.StringField):
    def validate(self, value):
        from ..submissions.models import Submission
        if value in Submission._fields.keys():
            self.error(
                'Form field name cannot be one of the disallowed field names')
        super(FormFieldNameField, self).validate(value)


# Forms
class FormField(db.EmbeddedDocument):
    '''A :class:`mongoengine.EmbeddedDocument` used in storing the
    Checklist/Critical Incident form questions in a
    :class:`core.documents.Form` model.

    Each :class:`core.documents.FormField` has attributes for specifying
    various behaviour for the form field.

    :attr:`analysis_type` which specifies the sort of data analysis to be
    performed on the field and is defined by the values stored
    in :attr:`ANALYSIS_TYPES`

    :attr:`represents_boolean` which is either True for a FormField that
    accepts only one value (e.g. Critical Incident form fields)

    :attr:`options` which is a dictionary that has keys representing
    field option values and values representing the option description.
    (e.g. {'1': 'Yes'})

    :attr:`allows_multiple_values` which is a boolean field specifying whether
    the field will accept multiple values as correct responses

    :attr:`min_value` which specifies the minimum accepted value and
    :attr:`max_value` for specifying the maximum valid value.

    :attr:`description` stores the textual description of the field.

    :attr:`name` is the question code used to identify the field (e.g. AA)'''

    ANALYSIS_TYPES = (
        ('N/A', _('Not Applicable')),
        ('PROCESS', _('Process Analysis')),
        ('RESULT', _('Results Analysis')))

    name = FormFieldNameField(required=True)
    description = db.StringField(required=True)
    max_value = db.IntField(default=9999)
    min_value = db.IntField(default=0)
    allows_multiple_values = db.BooleanField(default=False)
    is_comment_field = db.BooleanField(default=False)
    options = db.DictField()
    represents_boolean = db.BooleanField(default=False)
    analysis_type = db.StringField(choices=ANALYSIS_TYPES, default='N/A')


class FormGroup(db.EmbeddedDocument):
    '''The :class:`core.documents.FormGroup` model provides storage for form
    groups in a :class:`core.documents.Form` and are the organizational
    structure for form fields. Besides the :attr:`fields` attribute for storing
    form fields, there's also a :attr:`name` attribute for storing the name.'''

    name = db.StringField(required=True)
    slug = db.StringField(required=True)
    fields = db.ListField(db.EmbeddedDocumentField('FormField'))


class Form(db.Document):
    '''Primary storage for Checklist/Incident Forms.
    Defines the following attributes:

    :attr:`events` a list of references to :class:`core.documents.Event`
    objects defining which events this form is to be used in.

    :attr:`groups` storage for the form groups in the form.

    :attr:`form_type` for specifying the type of the form as described
    by :attr:`FORM_TYPES`.

    :attr:`prefix` determines the prefix for the form. This prefix is used in
    identifying which form is to be used in parsing incoming submissions.

    :attr:`name` is the name for this form.
    :attr:`party_mappings` uses field names as keys, party identifiers as
    values.
    :attr:`calculate_moe` is true if Margin of Error calculations are
    going to be computed on results for this form.'''

    FORM_TYPES = (
        ('CHECKLIST', _('Checklist Form')),
        ('INCIDENT', _('Incident Form')))

    name = db.StringField(required=True)
    prefix = db.StringField()
    form_type = db.StringField(choices=FORM_TYPES)
    require_exclamation = db.BooleanField(
        default=True,
        verbose_name=_('Require exclamation (!) mark in text message? (Does not apply to Checklist Forms)'))
    groups = db.ListField(db.EmbeddedDocumentField('FormGroup'))
    version_identifier = db.StringField()

    events = db.ListField(db.ReferenceField(
        Event, reverse_delete_rule=db.PULL))
    deployment = db.ReferenceField(Deployment)
    quality_checks = db.ListField(db.DictField())
    party_mappings = db.DictField()
    calculate_moe = db.BooleanField(default=False)
    accredited_voters_tag = db.StringField(verbose_name=_("Accredited Voters"))
    verifiable = db.BooleanField(default=False,
                                 verbose_name=_("Quality Assurance"))
    invalid_votes_tag = db.StringField(verbose_name=_("Invalid Votes"))
    registered_voters_tag = db.StringField(verbose_name=_("Registered Voters"))
    blank_votes_tag = db.StringField(verbose_name=_("Blank Votes"))
    permitted_roles = db.ListField(db.ReferenceField(
        Role, reverse_delete_rule=db.PULL), verbose_name=_("Permitted Roles"))

    meta = {
        'indexes': [
            ['prefix'],
            ['events'],
            ['events', 'prefix'],
            ['events', 'form_type'],
            ['deployment'],
            ['deployment', 'events']
        ]
    }

    def __unicode__(self):
        return self.name or u''

    @property
    def tags(self):
        if not hasattr(self, '_field_cache'):
            self._field_cache = {
                f.name: f for g in self.groups for f in g.fields}
        return sorted(self._field_cache.keys())

    # added so we don't always have to iterate over everything
    # in the (admittedly rare) cases we need a specific field
    def get_field_by_tag(self, tag):
        if not hasattr(self, '_field_cache'):
            self._field_cache = {
                f.name: f for g in self.groups for f in g.fields}
        return self._field_cache.get(tag)

    # see comment on get_field_by_tag
    def get_group_by_name(self, name):
        if not hasattr(self, '_group_cache'):
            self._group_cache = {g.name: g for g in self.groups}
        return self._group_cache.get(name)

    def clean(self):
        '''Ensures all :class: `core.documents.FormGroup` instances for this
        document have their slug set.'''
        for group in self.groups:
            if not group.slug:
                group.slug = unidecode(slugify_unicode(group.name)).lower()
        return super(Form, self).clean()

    def save(self, **kwargs):
        # overwrite version identifier
        self.version_identifier = uuid4().hex

        super(Form, self).save(**kwargs)
        # create permissions for roles
        Need.objects.filter(
            action='view_forms', items=self,
            deployment=self.deployment).delete()
        Need.objects.create(
            action='view_forms', items=[self], entities=self.permitted_roles,
            deployment=self.deployment)

    def update(self, **kwargs):
        # overwrite version identifier
        kwargs2 = kwargs.copy()
        kwargs2.update(set__version_identifier=uuid4().hex)

        return super(Form, self).update(**kwargs2)

    def hash(self):
        xform_data = etree.tostring(
            self.to_xml(),
            encoding='UTF-8',
            xml_declaration=True
        )
        m = hashlib.md5()
        m.update(xform_data)
        return "md5:%s" % m.hexdigest()

    def to_xml(self):
        root = HTML_E.html()
        head = HTML_E.head(HTML_E.title(self.name))
        data = E.data(id='-1')  # will be replaced with actual submission ID
        model = E.model(E.instance(data))

        body = HTML_E.body()
        model.append(E.bind(nodeset='/data/form_id', readonly='true()'))
        model.append(E.bind(nodeset='/data/version_id', readonly='true()'))

        form_id = etree.Element('form_id')
        form_id.text = unicode(self.id)

        version_id = etree.Element('version_id')
        version_id.text = self.version_identifier

        data.append(form_id)
        data.append(version_id)

        # set up identifiers
        data.append(E.device_id())
        data.append(E.subscriber_id())
        data.append(E.phone_number())

        device_id_bind = E.bind(nodeset='/data/device_id')
        device_id_bind.attrib['{%s}preload' % NSMAP['jr']] = 'property'
        device_id_bind.attrib['{%s}preloadParams' % NSMAP['jr']] = 'deviceid'

        subscriber_id_bind = E.bind(nodeset='/data/subscriber_id')
        subscriber_id_bind.attrib['{%s}preload' % NSMAP['jr']] = 'property'
        subscriber_id_bind.attrib['{%s}preloadParams' % NSMAP['jr']] = 'subscriberid'

        phone_number_bind = E.bind(nodeset='/data/phone_number')
        phone_number_bind.attrib['{%s}preload' % NSMAP['jr']] = 'property'
        phone_number_bind.attrib['{%s}preloadParams' % NSMAP['jr']] = 'phonenumber'

        model.append(device_id_bind)
        model.append(subscriber_id_bind)
        model.append(phone_number_bind)

        for group in self.groups:
            grp_element = E.group(E.label(group.name))
            for field in group.fields:
                data.append(etree.Element(field.name))
                path = '/data/{}'.format(field.name)
                # fields that carry options may be single- or multiselect
                if field.options:
                    # sort options by value
                    sorted_options = sorted(
                        field.options.iteritems(),
                        key=itemgetter(1)
                    )
                    if field.allows_multiple_values:
                        elem_fac = E.select
                        model.append(E.bind(nodeset=path, type='select'))
                    else:
                        elem_fac = E.select1
                        model.append(E.bind(nodeset=path, type='select1'))

                    field_element = elem_fac(
                        E.label(field.description),
                        ref=field.name
                    )

                    for key, value in sorted_options:
                        field_element.append(
                            E.item(E.label(key), E.value(unicode(value)))
                        )
                else:
                    if field.represents_boolean:
                        field_element = E.select1(
                            E.label(field.description),
                            E.item(E.label('True'), E.value('1')),
                            E.item(E.label('False'), E.value('0')),
                            ref=field.name
                        )
                        model.append(E.bind(nodeset=path, type='select1'))
                    elif field.is_comment_field:
                        field_element = E.input(
                            E.label(field.description),
                            ref=field.name)
                        model.append(E.bind(
                            nodeset=path,
                            type='string'))
                    else:
                        field_element = E.input(
                            E.label(field.description),
                            ref=field.name
                        )
                        model.append(E.bind(
                            nodeset=path,
                            type='integer',
                            constraint='. >= {} and . <= {}'.format(
                                field.min_value,
                                field.max_value
                            )
                        ))
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
            'label': field.name,
            'description': field.description,
            'analysis': field.analysis_type
        }

        if field.is_comment_field:
            data['component'] = 'textarea'

        elif not field.options:
            data['component'] = 'textInput'
            data['required'] = field.represents_boolean
            data['min'] = field.min_value
            data['max'] = field.max_value
        else:
            sorted_options = sorted(
                field.options.iteritems(), key=itemgetter(1))
            data['options'] = [s[0] for s in sorted_options]
            if field.allows_multiple_values:
                data['component'] = 'checkbox'
            else:
                data['component'] = 'radio'

        return data

    @classmethod
    def serialize_group(cls, group):
        field_data = []

        # add group's description
        field_data.append({
            'label': group.name,
            'component': 'group',
        })

        field_data.extend([cls.serialize_field(f) for f in group.fields])

        return field_data

    @classmethod
    def serialize(cls, form):
        group_data = []
        for group in form.groups:
            group_data.extend(cls.serialize_group(group))
        data = {'fields': group_data}
        return data

    @classmethod
    def deserialize(cls, form, data):
        groups = []

        # verify that first field is always a group
        if len(data['fields']) > 0:
            if data['fields'][0]['component'] != 'group':
                # no group was created, create a default
                group = FormGroup(
                    name=_('Default Group'),
                    slug=unidecode(slugify_unicode(str(_('Default Group')))))
                groups.append(group)

        for f in data['fields']:
            if f['component'] == 'group':
                group = FormGroup(
                    name=f['label'],
                    slug=unidecode(slugify_unicode(f['label']))
                )
                groups.append(group)
                continue

            field = FormField(
                name=f['label'],
                description=f['description'],
            )

            if f['analysis']:
                field.analysis_type = f['analysis']

            if f['component'] == 'textarea':
                field.is_comment_field = True
                field.analysis_type = 'N/A'  # is always False
            elif f['component'] == 'textInput':
                field.represents_boolean = f['required']
                if f['min']:
                    field.min_value = f['min']
                if f['max']:
                    field.max_value = f['max']
            else:
                field.options = {k: v for v, k in enumerate(f['options'], 1)}

                if f['component'] == 'checkbox':
                    field.allows_multiple_values = True

            group.fields.append(field)

        form.groups = groups

        # frag the field cache so it's regenerated
        try:
            delattr(form, '_field_cache')
        except AttributeError:
            pass
        form.save()
