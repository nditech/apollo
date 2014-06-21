from ..core import db
from ..deployments.models import Deployment, Event
from flask.ext.babel import lazy_gettext as _
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
        binding_elements = []
        schema_elements = []
        for tag in self.tags:
            field = self.get_field_by_tag(tag)
            path = '/data/{}'.format(tag)
            bind_element = E.bind(nodeset=path, type='int')
            if field.options:
                if field.allows_multiple_values:
                    sc_elem_fac = E.select
                else:
                    sc_elem_fac = E.select1

                sc_element = sc_elem_fac(E.label(field.description), ref=tag)
                for key in sorted(field.options.keys()):
                    sc_element.append(E.item(
                        E.label(key),
                        E.value(unicode(field.options[key]))
                    ))
            else:
                sc_element = E.input(E.label(field.description), ref=tag)

            binding_elements.append(bind_element)
            schema_elements.append(sc_element)

        return binding_elements, schema_elements
