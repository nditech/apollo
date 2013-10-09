from django.conf import settings
from django.core.cache import cache as default_cache
from django.core.cache import get_cache, InvalidCacheBackendError
from django.contrib.gis.db import models
from django.dispatch import receiver
from django_dag.models import Graph, Node, Edge
from django_dag.mixins import GraphMixin
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from djorm_hstore.fields import DictionaryField
from djorm_hstore.models import HStoreManager
from rapidsms.models import Contact, Backend, Connection
from datetime import datetime
from apollo.core.managers import SubmissionManager, ObserverManager
import networkx as nx
import operator as op
from parsimonious.grammar import Grammar
import reversion
import ast
import re
from unidecode import unidecode
import vinaigrette


LOCATIONTYPE_GRAPH = None
LOCATION_GRAPH = None


def locationtype_graph():
    global LOCATIONTYPE_GRAPH
    if not LOCATIONTYPE_GRAPH:
        LOCATIONTYPE_GRAPH, _ = Graph.objects.get_or_create(name='location_type')
    return LOCATIONTYPE_GRAPH


def location_graph():
    global LOCATION_GRAPH
    if not LOCATION_GRAPH:
        LOCATION_GRAPH, _ = Graph.objects.get_or_create(name='location')
    return LOCATION_GRAPH


class LocationType(GraphMixin):
    """Location Type"""
    name = models.CharField(max_length=100)
    # code is used mainly in the SMS processing logic
    code = models.CharField(blank=True, max_length=10, db_index=True)
    on_display = models.BooleanField(default=False, help_text=_("Controls the display of this location type on the form lists"))
    on_dashboard = models.BooleanField(default=False, help_text=_("Controls the display of this location type on the dashboard filter"))
    on_analysis = models.BooleanField(default=False, help_text=_("Controls the display of this location type on the analysis filter"))
    in_form = models.BooleanField(default=False, db_index=True, help_text=_("Determines whether this LocationType can be used in SMS forms"))

    def __unicode__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        self.default_graph = locationtype_graph()
        return super(LocationType, self).__init__(*args, **kwargs)

    @staticmethod
    def root():
        # retrieves the root location type
        try:
            return Location.root().type
        except IndexError, AttributeError:
            pass


class Location(GraphMixin):
    """Location"""
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=100, db_index=True, blank=True)
    type = models.ForeignKey(LocationType)
    data = DictionaryField(db_index=True, null=True, blank=True)
    poly = models.PolygonField(null=True, blank=True)

    objects = models.GeoManager()
    hstore = HStoreManager()

    def __unicode__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        self.default_graph = location_graph()
        return super(Location, self).__init__(*args, **kwargs)

    def sub_location_types(self):
        return self.type.get_children()

    def _get_locations_graph(self, reverse=False):
        if reverse:
            if not hasattr(Location, '_reversed_locations_graph'):
                Location._reversed_locations_graph = get_locations_graph(reverse=True)
            return Location._reversed_locations_graph
        else:
            if not hasattr(Location, '_locations_graph'):
                Location._locations_graph = get_locations_graph(reverse=False)
            return Location._locations_graph

    def nx_ancestors(self, include_self=False):
        graph = self._get_locations_graph()
        ancestor_ids = nx.topological_sort(graph, graph.subgraph(nx.dfs_tree(graph, self.id).nodes()).nodes())
        if include_self:
            return [graph.node[id] for id in ancestor_ids]
        else:
            return [graph.node[id] for id in ancestor_ids if id != self.id]

    def nx_descendants(self, include_self=False):
        reversed_graph = self._get_locations_graph(reverse=True)
        descendant_ids = nx.topological_sort(reversed_graph, reversed_graph.subgraph(nx.dfs_tree(reversed_graph, self.id).nodes()).nodes())
        if include_self:
            return [reversed_graph.node[id] for id in descendant_ids]
        else:
            return [reversed_graph.node[id] for id in descendant_ids if id != self.id]

    def nx_children(self):
        reversed_graph = self._get_locations_graph(reverse=True)
        children_ids = reversed_graph.successors(self.id)
        return [reversed_graph.node[id] for id in children_ids]

    @staticmethod
    def root():
        # retrieves the root location
        try:
            root = Location.objects.all()[0].nx_ancestors(include_self=True)[-1]
            return Location.objects.get(pk=root.get('id'))
        except IndexError:
            pass


def get_locations_graph(reverse=False):
    '''
    This provides a means of caching the generated
    graph and serving up the graph from the cache
    as needed.

    There's an optional parameter to retrieve the
    reversed version of the graph
    '''
    try:
        cache = get_cache('graphs')
    except InvalidCacheBackendError:
        cache = default_cache

    graph = cache.get('reversed_locations_graph') if reverse else cache.get('locations_graph')
    if not graph:
        if reverse:
            graph = generate_locations_graph().reverse()
            cache.set('reversed_locations_graph', graph, settings.LOCATIONS_GRAPH_MAXAGE)
        else:
            graph = generate_locations_graph()
            cache.set('locations_graph', graph, settings.LOCATIONS_GRAPH_MAXAGE)
    return graph


def get_location_ancestors_by_type(graph, location_id, types=[]):
    '''
    This method provides a means of retrieving the ancestors of a particular location
    of specified types as defined in the LocationType model. It uses the depth-first-search
    algorithm in retrieving this subgraph

    types is a list of location_types names
    '''
    nodes = graph.subgraph(nx.dfs_tree(graph, location_id).nodes()).nodes(data=True)
    return [node[1] for node in nodes if node[1]['type'].lower() in map(unicode.lower, map(unicode, types)) or not types]


def get_location_ancestor_by_type(graph, location_id, location_type):
    '''
    Convenience method to enable retrievel of just one location_type
    '''
    return get_location_ancestors_by_type(graph, location_id, types=[location_type])


def generate_locations_graph():
    '''
    Creates a directed acyclical graph of the locations database
    This is more performant for performing tree lookups and is
    faster than the alternative of running several queries to
    retrieve this graph from the database
    '''
    nodes = Node.objects.filter(graph__name='location').values('pk', 'object_id')
    locations = Location.objects.filter(pk__in=[node['object_id'] for node in nodes]).values('pk', 'name', 'type__name')
    DG = nx.DiGraph()
    for location in locations:
        DG.add_node(location['pk'], name=location['name'], type=location['type__name'], id=location['pk'])
    edges = Edge.objects.filter(graph__name='location').values_list('node_from__object_id', 'node_to__object_id')
    for node_from, node_to in edges:
        DG.add_edge(node_from, node_to)
    return DG


class Partner(models.Model):
    name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=50)

    def __unicode__(self):
        return self.abbr

    class Meta:
        ordering = ['abbr']


class ObserverRole(models.Model):
    """Roles"""
    name = models.CharField(max_length=100, db_index=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Observer(models.Model):
    """Election Observer"""
    GENDER = (
        ('M', _('Male')),
        ('F', _('Female')),
        # Translators: the next string describes a gender that isn't specified
        ('U', _('Unspecified')),
    )
    observer_id = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    contact = models.OneToOneField(Contact, related_name='observer', blank=True, null=True)
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location, related_name="observers")
    supervisor = models.ForeignKey('self', null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER, db_index=True)
    partner = models.ForeignKey(Partner, null=True, blank=True)
    data = DictionaryField(db_index=True, null=True, blank=True)
    last_connection = models.ForeignKey(Connection, null=True, blank=True)

    objects = ObserverManager()

    def _get_phone(self):
        return self.contact.connection_set.all()[settings.DEFAULT_CONNECTION_INDEX].identity \
            if self.contact and self.contact.connection_set.count() else None

    def _set_phone(self, phone):
        if phone:
            for backend in Backend.objects.all():
                try:
                    conn = Connection.objects.get(identity=phone, backend=backend)
                    conn.contact = self.contact
                    conn.save()
                except Connection.DoesNotExist:
                    conn, _ = Connection.objects.get_or_create(
                        backend=backend,
                        identity=phone)
                    conn.contact = self.contact
                    conn.save()

    phone = property(_get_phone, _set_phone)

    class Meta:
        ordering = ['observer_id']
        permissions = (
            ("view_observers", "Can view observers"),
            ("export_observers", "Can export observers"),
            ("message_observers", "Can message observers"),
        )

    def __unicode__(self):
        return u"%s" % (self.name or "",)


class AbstractDataField(models.Model):
    class Meta:
        abstract = True


class ObserverDataField(AbstractDataField):
    name = models.CharField(max_length=32)  # will allow name to double as key
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Activity(models.Model):
    '''The activity model is used for grouping forms into one activity
    for instance, critical incident forms and checklists for a particular
    election exercise, constitute an activity'''
    name = models.CharField(max_length=100)
    start_date = models.DateField(default=datetime.today())
    end_date = models.DateField(default=datetime.today())
    forms = models.ManyToManyField('Form', related_name='activities')

    def __unicode__(self):
        return u"{}".format(self.name)

    @staticmethod
    def default():
        activities = Activity.objects.filter(start_date__lte=datetime.today(), end_date__gte=datetime.today()).order_by('-start_date')
        if activities:
            return activities[0]
        activities = Activity.objects.filter(end_date__lte=datetime.today()).order_by('-end_date')
        if activities:
            return activities[0]
        activities = Activity.objects.filter(start_date__gte=datetime.today()).order_by('start_date')
        if activities:
            return activities[0]
        else:
            return None

    @staticmethod
    def for_today():
        activities = Activity.objects.filter(start_date__lte=datetime.today(), end_date__gte=datetime.today()).order_by('-start_date')
        if activities:
            return activities[0]
        else:
            raise Activity.DoesNotExist

    class Meta:
        permissions = (
            ("view_activities", "Can view all activities"),
        )
        verbose_name_plural = 'activities'


class Form(models.Model):
    '''
    Defines the schema for forms that will be managed
    by the application. Of important note are the
    `trigger` and `field_pattern` fields.

    `trigger` stores a regular expression that matches
    the entire text message string (after preliminary
    sanitization) and must contain a "fields" group
    match. This enables the parser to locate the
    section that handles fields parsing. Optionally,
    the `trigger` may contain a "observer" group that
    specifies the string pattern used in searching for
    the observer.

    It's most likely that the pattern for the "fields"
    group will match with that of `field_pattern`. This
    parameter is used to locate other fields that may
    parse correctly in the general form matching phase
    but not be a valid field in the individual field
    parsing phase.

    `field_pattern` must be defined to include groups with
    the names: "key" representing the field tag and "value"
    representing the expected value.
    '''
    FORM_TYPES = (
        ('CHECKLIST', _('Checklist')),
        ('INCIDENT', pgettext_lazy('Critical Incident', 'Incident')),
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, choices=FORM_TYPES, default='CHECKLIST')
    trigger = models.CharField(max_length=255, unique=True)
    field_pattern = models.CharField(max_length=255)
    autocreate_submission = models.BooleanField(default=False,
        help_text=_("Whether to create a new record if a submission doesn't exist"))
    options = DictionaryField(db_index=True, null=True, blank=True, default='')

    objects = HStoreManager()

    def __unicode__(self):
        return self.name

    def match(self, text):
        if self.trigger and re.match(self.trigger, text, flags=re.I):
            return True

    class Meta:
        permissions = (
            ("view_form", "Can view form"),
        )

    @staticmethod
    def parse(text):
        text = unidecode(text)
        forms = Form.objects.all()
        submission = {'data': {}}
        observer = None

        # iterate over all forms, until we get a match
        for form in forms:
            if form.match(text):
                match = re.match(form.trigger, text, flags=re.I)
                fields_text = match.group('fields')

                if 'observer' in match.groupdict().keys():
                    try:
                        observer = Observer.objects.get(observer_id=match.group('observer'))
                    except Observer.DoesNotExist:
                        pass

                # begin submission processing
                submission['form'] = form
                submission['range_error_fields'] = []
                submission['attribute_error_fields'] = []

                '''
                In each loop, each field is expected to parse
                their own values out and remove their tags from
                the field text. If any text is left after parsing
                every field, then we're likely to have a field
                attribute error
                '''
                for group in form.groups.all():
                    for field in group.fields.all():
                        fields_text = field.parse(fields_text)
                        if field.value == -1:
                            submission['range_error_fields'].append(field.tag)

                        # this prevents a situation where 0 (a valid input) is ignored
                        elif field.value != None:
                            submission['data'][field.tag.upper()] = unicode(field.value)
                if fields_text:
                    for field in re.finditer(form.field_pattern, fields_text, flags=re.I):
                        submission['attribute_error_fields'].append(field.group('key'))
                break
        else:
            raise Form.DoesNotExist
        return (submission, observer)

    def get_verification_flags(self):
        _flags = self.options.get('verification_flags', '')
        if _flags:
            flags = ast.literal_eval(_flags)
            return flags
        else:
            return []

    def get_verification_flag_attributes(self, attribute):
        return [flag.get(attribute, None) for flag in self.get_verification_flags()]

    def contestants(self):
        if self.options.get('party_votes', None):
            return ast.literal_eval(self.options.get('party_votes'))

    def parties(self):
        contestants = self.contestants()
        if contestants:
            return [unicode(party) for party, code in contestants]

    def votes(self):
        contestants = self.contestants()
        if contestants:
            return [unicode(code) for party, code in contestants]



class FormGroup(models.Model):
    name = models.CharField(max_length=32, blank=True)
    abbr = models.CharField(max_length=32, blank=True, null=True, help_text=_("Abbreviated version of the group name"))
    form = models.ForeignKey(Form, related_name='groups')

    class Meta:
        order_with_respect_to = 'form'

    def __unicode__(self):
        return self.name


class FormField(models.Model):
    ANALYSIS_TYPES = (
        ('', _('N/A')),
        ('PROCESS', _('Process')),
        ('VOTE', _('Candidate Vote')),
    )

    name = models.CharField(max_length=32)
    description = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(FormGroup, related_name='fields')
    tag = models.CharField(max_length=8)
    upper_limit = models.IntegerField(null=True, default=9999)
    lower_limit = models.IntegerField(null=True, default=0)
    present_true = models.BooleanField(default=False)
    allow_multiple = models.BooleanField(default=False)
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES, db_index=True, blank=True, default='')

    value = None

    class Meta:
        order_with_respect_to = 'group'

    def __unicode__(self):
        return '%s -> %s' % (self.group, self.tag,)

    def parse(self, text):
        pattern = r'{0}(?P<value>\d*)'.format(self.tag)

        match = re.search(pattern, text, re.I)

        if match:
            if self.allow_multiple:
                # for a match value like '23', produce a list with
                # 2 and 3 as `field_values`
                field_values = [int(i) for i in list(match.group('value'))] \
                    if match.group('value') else None

                if field_values != None:
                    options = self.options.all()

                    allowed_values = [option.option for option in options] if options else None

                    for item in field_values:
                        # check that all the values are allowed options
                        if allowed_values and (item not in allowed_values):
                            self.value = -1
                            break

                        # and they're within the specified limits
                        if item < self.lower_limit or item > self.upper_limit:
                            self.value = -1
                            break

                    if self.value != -1:
                        self.value = ','.join(map(str, field_values))
            else:
                field_value = int(match.group('value')) \
                    if match.group('value') else None

                if field_value != None:
                    if self.options.all().count():
                        for option in self.options.all():
                            if option.option == field_value:
                                self.value = field_value
                                break
                        else:
                            self.value = -1
                    else:
                        if field_value < self.lower_limit or field_value > self.upper_limit:
                            self.value = -1
                        else:
                            self.value = field_value
                elif self.present_true:
                    # a value of 1 indicates presence/truth
                    self.value = 1

        return re.sub(pattern, '', text, flags=re.I) if self.value != None else text


class VoteOption(models.Model):
    form = models.ForeignKey(Form, related_name='vote_options')
    field = models.ForeignKey(FormField)
    abbr = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.abbr


class FormFieldOption(models.Model):
    field = models.ForeignKey(FormField, related_name="options")
    description = models.CharField(max_length=255)
    option = models.PositiveIntegerField()

    class Meta:
        order_with_respect_to = 'field'

    def __unicode__(self):
        return '%s -> %s' % (self.field, self.option,)


class Submission(models.Model):
    form = models.ForeignKey(Form, related_name='submissions')
    observer = models.ForeignKey(Observer, blank=True, null=True)
    location = models.ForeignKey(Location, related_name="submissions")
    master = models.ForeignKey('self', null=True, blank=True, related_name='submissions')
    date = models.DateField(default=datetime.today())
    data = DictionaryField(db_index=True, null=True, blank=True)
    overrides = DictionaryField(db_index=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SubmissionManager()

    def __unicode__(self):
        return u"%s -> %s" % (self.pk, self.observer,)

    class Meta:
        permissions = (
            ("view_submissions", "Can view submissions"),
            ("export_submissions", "Can export submissions"),
            ("can_analyse", "Can access submission analyses"),
            ("can_verify", "Can access submission verifications"),
        )

    @property
    def siblings(self):
        if hasattr(self, '_siblings'):
            return self._siblings
        else:
            self._siblings = Submission.objects.exclude(pk=self.pk).exclude(observer=None).filter(location=self.location, date=self.date, form=self.form)
        return self._siblings

    def _get_completion(self, group):
        tags = group.fields.values_list('tag', flat=True)
        truthy = []
        for tag in tags:
            if tag in self.data or tag in getattr(self.master, 'data', {}):
                truthy.append(True)
            else:
                truthy.append(False)
        return truthy

    def is_complete(self, group):
        truthy = self._get_completion(group)
        if truthy is None:
            return None
        return all(truthy)

    def is_partial(self, group):
        truthy = self._get_completion(group)
        if truthy is None:
            return None
        return any(truthy)

    def is_missing(self, group):
        truthy = self._get_completion(group)
        if truthy is None:
            return None
        return not any(truthy)

    def get_location_for_type(self, location_type):
        locations = filter(lambda x: x['type'] == location_type.name, self.location.nx_ancestors(include_self=True))
        if locations:
            return Location.objects.get(pk=locations[0]['id'])
        else:
            return None


class Sample(models.Model):
    '''Used for grouping locations into samples'''
    name = models.CharField(max_length=100)
    locations = models.ManyToManyField(Location, related_name='samples')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


# Parsers for Checklist Verification

class Evaluator(object):
    def __init__(self, env={}):
        self.env = env
        self.scratch = None  # for storing temporary results

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                      if '__' not in k and hasattr(v, '__doc__') and v.__doc__)
        return Grammar(grammar).parse(source)

    def eval(self, source):
        node = self.parse(source) if isinstance(source, str) or isinstance(source, unicode) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def expr(self, node, children):
        'expr = operand operation*'
        operand, operation = children
        self.scratch = None
        try:
            return children[1][-1]
        except IndexError:
            return operand

    def operand(self, node, children):
        'operand = _ (variable / number) _'
        _, value, _ = children
        if self.scratch == None:
            self.scratch = value[0]
        return value[0]

    def operation(self, node, children):
        'operation = operator operand'
        operator, operand = children
        self.scratch = operator(self.scratch, operand)
        return self.scratch

    def operator(self, node, children):
        'operator = "+" / "-" / "*" / "/"'
        operators = {'+': op.add, '-': op.sub, '*': op.mul, '/': op.div}
        return operators[node.text]

    def variable(self, node, children):
        'variable = ~"[a-z]+"i _'
        return float(self.env.get(node.text.strip()))

    def number(self, node, children):
        'number = ~"\-?[0-9\.]+"'
        return float(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'
        pass


class Comparator(object):
    def __init__(self):
        self.param = None

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                      if '__' not in k and hasattr(v, '__doc__') and v.__doc__)
        return Grammar(grammar).parse(source)

    def eval(self, source, param=None):
        if param != None:
            self.param = float(param)
        node = self.parse(source) if isinstance(source, str) or isinstance(source, unicode) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def expr(self, node, children):
        'expr = operator _ number'
        operator, _, number = children
        return operator(self.param, number)

    def operator(self, node, children):
        'operator = ">=" / "<=" / ">" / "<" / "="'
        operators = {'>': op.gt, '>=': op.ge, '<': op.lt, '<=': op.le, '=': op.eq}
        return operators[node.text]

    def number(self, node, children):
        'number = ~"\-?[0-9\.]+"'
        return float(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'
        pass


# auto create Contacts when an observer is created
@receiver(models.signals.post_save, sender=Observer, dispatch_uid='create_contact')
def create_contact(sender, **kwargs):
    if kwargs['created']:
        contact = Contact.objects.create()
        kwargs['instance'].contact = contact
        kwargs['instance'].save()


# if an observer gets deleted, also delete the associated contact
@receiver(models.signals.post_delete, sender=Observer, dispatch_uid='delete_contact')
def delete_contact(sender, **kwargs):
    if kwargs['instance'].contact:
        kwargs['instance'].contact.delete()


# the below function generates a comparison function
def make_value_check(a):
    def value_check(b):
        # perform exclusive or operation
        if bool(a) ^ bool(b):
            return 0  # either but not both values exist
        if a == b:
            return 1  # values match
        return -1  # value exists but doesn't match

    return value_check


@receiver(models.signals.post_save, sender=Submission, dispatch_uid='create_or_sync_master')
def create_or_sync_master(sender, **kwargs):
    instance = kwargs['instance']

    if kwargs['created']:
        master = instance.master
        # we only want to create a submission that will be assigned
        # as the master if this is not already a master submission
        if not master and instance.observer and instance.form.type == 'CHECKLIST':
            # create the master
            master = Submission.objects.create(
                    form=instance.form,
                    observer=None,
                    location=instance.location,
                    date=instance.date,
                    data=instance.data,
                    created=instance.created,
                    updated=instance.updated
                )
            instance.master = master
            instance.save()
    else:
        # quit if this is the master
        if instance.observer is None:
            return True

        # grab sibling and master checklists
        siblings = list(instance.siblings)
        master = instance.master

        if master is None or master == instance:
            return True

        # if no siblings exist, copy to master and quit
        if not siblings:
            for key in instance.data.keys():
                if key in master.overrides:
                    continue
                master.data[key] = instance.data[key]

            master.save()
            return True

        # get all possible keys
        key_set = set(instance.data.keys())
        for sibling in siblings:
            key_set.update(sibling.data.keys())

        # this be pure hackery
        for key in key_set:
            # if the key has already been overridden, don't do anything
            if key in master.overrides:
                continue

            # get the value set for this key, and create a comparison function
            # for that value (see make_value_check definition).
            current = instance.data.get(key, None)
            checker_function = make_value_check(current)

            # the map() call executes the inner value_check function with a = current
            # and b = each item from the list comprehension
            checked_values = map(checker_function, [sibling.data.get(key, None) for sibling in siblings])

            if -1 in checked_values:
                # only if the key is set to different values across all siblings
                master.data.pop(key, None)
                continue

            if current is not None:
                # if the key has not been set on the master and this instance
                # has it set
                master.data[key] = current

        master.save()


@receiver(models.signals.post_save, sender=Location, dispatch_uid='invalidate_locations_cache')
def invalidate_locations_cache(sender, **kwargs):
    try:
        delattr(Location, '_reversed_locations_graph')
    except AttributeError:
        pass
    try:
        delattr(Location, '_locations_graph')
    except AttributeError:
        pass
    try:
        cache = get_cache('graphs')
    except InvalidCacheBackendError:
        cache = default_cache
    cache.delete('reversed_locations_graph')
    cache.delete('locations_graph')


@receiver(models.signals.pre_save, sender=Submission, dispatch_uid='compute_verification')
def compute_verification(sender, **kwargs):
    verified_flag = settings.FLAG_STATUSES['verified'][0]
    rejected_flag = settings.FLAG_STATUSES['rejected'][0]

    instance = kwargs['instance']
    comparator = Comparator()

    NO_DATA = 0
    OK = 1
    UNOK = 2

    if instance.observer == None:
        flags_statuses = []
        for flag in instance.form.get_verification_flags():
            evaluator = Evaluator(instance.data)
            try:
                lvalue = evaluator.eval(flag['lvalue'])
                rvalue = evaluator.eval(flag['rvalue'])
                if flag['comparator'] == 'pctdiff':
                    try:
                        diff = abs(lvalue - rvalue) / float(max([lvalue, rvalue]))
                    except ZeroDivisionError:
                        diff = 0
                elif flag['comparator'] == 'pct':
                    try:
                        diff = float(lvalue) / float(rvalue)
                    except ZeroDivisionError:
                        diff = 0
                else:
                    # value-based comparator
                    diff = abs(lvalue - rvalue)

                # evaluate conditions and set flag appropriately
                if comparator.eval(flag['okay'], diff):
                    instance.data[flag['storage']] = settings.FLAG_STATUSES['no_problem'][0]
                    flags_statuses.append(OK)
                elif comparator.eval(flag['serious'], diff):
                    instance.data[flag['storage']] = settings.FLAG_STATUSES['serious_problem'][0]
                    flags_statuses.append(UNOK)
                elif comparator.eval(flag['problem'], diff):
                    instance.data[flag['storage']] = settings.FLAG_STATUSES['problem'][0]
                    flags_statuses.append(UNOK)
                else:
                    # if we have no way of determining, we assume it's okay
                    instance.data[flag['storage']] = settings.FLAG_STATUSES['no_problem'][0]
                    flags_statuses.append(OK)
            except TypeError:
                # no sufficient data
                try:
                    del instance.data[flag['storage']]
                except KeyError:
                    pass
                flags_statuses.append(NO_DATA)

        # compare all flags and depending on the values, set the status
        if not instance.data.get('verification', None) in [verified_flag, rejected_flag]:
            if all(map(lambda i: i == NO_DATA, flags_statuses)):
                try:
                    del instance.data['verification']
                except KeyError:
                    pass
            elif any(map(lambda i: i == UNOK, flags_statuses)):
                instance.data['verification'] = settings.FLAG_STATUSES['problem'][0]
            elif any(map(lambda i: i == OK, flags_statuses)):
                instance.data['verification'] = settings.FLAG_STATUSES['no_problem'][0]

# model translation registrations
vinaigrette.register(LocationType, ['name'])
vinaigrette.register(ObserverRole, ['name'])
vinaigrette.register(ObserverDataField, ['name'])
vinaigrette.register(Activity, ['name'])
vinaigrette.register(Form, ['name'])
vinaigrette.register(FormGroup, ['name', 'abbr'])
vinaigrette.register(FormField, ['description'])
vinaigrette.register(FormFieldOption, ['description'])
vinaigrette.register(Sample, ['name'])

# reversion
try:
    reversion.register(Submission, follow=('master',))
except reversion.revisions.RegistrationError:
    pass