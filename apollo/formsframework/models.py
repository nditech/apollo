from operator import itemgetter
from ..core import db
from ..deployments.models import Deployment, Event
from flask.ext.babel import lazy_gettext as _
from lxml import etree
from lxml.builder import E, ElementMaker
from slugify import slugify_unicode


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

    name = db.StringField(required=True)
    description = db.StringField(required=True)
    max_value = db.IntField(default=9999)
    min_value = db.IntField(default=0)
    allows_multiple_values = db.BooleanField(default=False)
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
    :attr:`party_mappings` uses party identifiers as keys, field names as
    values.
    :attr:`calculate_moe` is true if Margin of Error calculations are
    going to be computed on results for this form.'''

    FORM_TYPES = (
        ('CHECKLIST', _('Checklist Form')),
        ('INCIDENT', _('Incident Form')))

    name = db.StringField(required=True)
    prefix = db.StringField()
    form_type = db.StringField(choices=FORM_TYPES)
    groups = db.ListField(db.EmbeddedDocumentField('FormGroup'))

    events = db.ListField(db.ReferenceField(
        Event, reverse_delete_rule=db.PULL))
    deployment = db.ReferenceField(Deployment)
    quality_checks = db.ListField(db.DictField())
    party_mappings = db.DictField()
    calculate_moe = db.BooleanField(default=False)
    accredited_voters_tag = db.StringField()
    verifiable = db.BooleanField(default=False)
    invalid_votes_tag = db.StringField()
    registered_voters_tag = db.StringField()

    meta = {
        'indexes': [
            ['prefix'],
            ['events'],
            ['events', 'prefix'],
            ['events', 'form_type']
        ]
    }

    def __unicode__(self):
        return self.name

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
                group.slug = slugify_unicode(group.name).lower()
        return super(Form, self).clean()

    def to_xml(self):
        root = HTML_E.html()
        head = HTML_E.head(HTML_E.title(self.name))
        data = E.data(id='-1')  # will be replaced with actual submission ID
        model = E.model(E.instance(data))

        body = HTML_E.body()
        model.append(E.bind(nodeset='/data/form_id', readonly='true()'))
        form_id = etree.Element('form_id')
        form_id.text = unicode(self.id)
        data.append(form_id)

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
