from apollo.core import db, cache
from apollo.deployments.models import Deployment, Event
from flask.ext.mongoengine import BaseQuerySet
from slugify import slugify_unicode
from mongoengine import Q


class LocationQuerySet(BaseQuerySet):
    '''Custom queryset class for filtering locations under a specified
    location.'''
    def filter_in(self, location):
        '''
        Filters out locations that are not descendants of :param: `location`
        '''
        return self(Q(id=location.id) | Q(ancestors_ref=location))


# Locations
class Sample(db.Document):
    '''Samples allow for the storage of groups of Locations that can be used
    to create samples for analysis or data management.'''

    name = db.StringField()

    event = db.ReferenceField(Event)
    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['event'],
            ['deployment'],
            ['deployment', 'event']
        ]
    }


class LocationTypeAncestor(db.EmbeddedDocument):
    '''An embedded document used by the :class:`core.document.LocationType`
    model for storing denormalized ancestry data'''

    name = db.StringField()


class LocationType(db.Document):
    '''Stores the type describing the administrative level of a Location
    :attr ancestors_ref: This stores a list references to ancestor
    loction types as documented in
    http://docs.mongodb.org/manual/tutorial/model-tree-structures/'''

    name = db.StringField()
    ancestors_ref = db.ListField(db.ReferenceField(
        'LocationType', reverse_delete_rule=db.PULL))
    ancestor_count = db.IntField()
    is_administrative = db.BooleanField(default=False)
    is_political = db.BooleanField(default=False)
    has_registered_voters = db.BooleanField(db_field='has_rv', default=False)
    has_political_code = db.BooleanField(db_field='has_pc', default=False)
    has_other_code = db.BooleanField(db_field='has_oc', default=False)
    metafields = db.ListField(db.StringField())
    slug = db.StringField()

    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['deployment']
        ]
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    @classmethod
    def root(cls):
        return cls.objects.get(__raw__={'ancestors_ref': []})

    def clean(self):
        if not self.slug:
            self.slug = slugify_unicode(self.name).lower()
        self.ancestor_count = len(self.ancestors_ref)
        return super(LocationType, self).clean()

    @property
    def children(self):
        """Returns a list of descendants sorted by the length of the
        `attr`ancestors_ref.
        """
        temp = LocationType.objects(ancestors_ref=self)
        return sorted(temp, None, lambda x: len(x.ancestors_ref))

    def __unicode__(self):
        return self.name or u''


class Location(db.DynamicDocument):

    '''A store for Locations'''

    name = db.StringField()
    code = db.StringField()
    political_code = db.StringField(db_field='pcode')
    other_code = db.StringField(db_field='ocode')
    location_type = db.StringField()
    coords = db.GeoPointField()
    registered_voters = db.LongField(db_field='rv', default=0)
    ancestor_count = db.IntField(default=0)
    ancestors_ref = db.ListField(db.ReferenceField(
        'Location', reverse_delete_rule=db.PULL))
    samples = db.ListField(db.ReferenceField(
        'Sample', reverse_delete_rule=db.PULL))
    events = db.ListField(db.ReferenceField(
        Event, reverse_delete_rule=db.PULL))
    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['ancestors_ref'],
            ['ancestors_ref', 'location_type'],
            ['samples'],
            ['events'],
            ['location_type'],
            ['name'],
            ['name', 'location_type'],
            ['code'],
            ['political_code'],
            ['events', 'code'],
            ['deployment'],
            ['deployment', 'events']
        ],
        'queryset_class': LocationQuerySet
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    @classmethod
    def root(cls):
        return cls.objects.get(__raw__={'ancestors_ref': []})

    @property
    def children(self):
        return Location.objects(
            ancestors_ref__all=self.ancestors_ref + [self],
            ancestors_ref__size=len(self.ancestors_ref) + 1)

    @property
    def descendants(self):
        return Location.objects(ancestors_ref=self)

    @property
    def ancestors(self):
        return self.ancestors_ref

    def ancestor(self, location_type, include_self=True):
        try:
            return filter(lambda l: l.location_type == location_type,
                          self.ancestors_ref + [self] if include_self else
                          self.ancestors_ref)[0]
        except IndexError:
            pass

    def __unicode__(self):
        return self.name or u''

    def save(self, *args, **kwargs):
        from . import LocationsService
        cache.delete_memoized(LocationsService.registered_voters_map)
        return super(Location, self).save(*args, **kwargs)

    def _update_ancestor_count(self, save=False):
        if self.ancestor_count != len(self.ancestors_ref):
            self.ancestor_count = len(self.ancestors_ref)

        if save:
            self.update(set__ancestor_count=self.ancestor_count)

    def clean(self):
        self._update_ancestor_count()
