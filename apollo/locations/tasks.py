import cachetools
from flask import render_template_string
from flask.ext.babel import lazy_gettext as _
from hashlib import sha256
from slugify import slugify

import pandas as pd

from .. import helpers, services
from ..factory import create_celery_app
from ..messaging.tasks import send_email

celery = create_celery_app()

email_template = '''
Notification
------------

Your location import task has been completed.
'''

class LocationCache():
    cache = cachetools.LFUCache(maxsize=50)

    def _cache_key(self, location_code, location_type, location_name):
        # remove smart quotes
        location_code = unicode(location_code).replace(
            u"\u2018", "").replace(
            u"\u2019", "").replace(u"\u201c", "").replace(u"\u201d", "")
        location_type = unicode(location_type).replace(
            u"\u2018", "").replace(
            u"\u2019", "").replace(u"\u201c", "").replace(u"\u201d", "")
        location_name = unicode(location_name).replace(
            u"\u2018", "").replace(
            u"\u2019", "").replace(u"\u201c", "").replace(u"\u201d", "")
        return sha256(
            '{}:{}:{}'.format(
                location_code, location_type, location_name)).hexdigest()

    def get(self, location_code, location_type, location_name):
        cache_key = self._cache_key(
            location_code, location_type, location_name)
        return self.cache.get(cache_key, None)

    def has(self, location_code, location_type, location_name):
        cache_key = self._cache_key(
            location_code, location_type, location_name)
        return cache_key in self.cache

    def set(self, location_obj):
        cache_key = self._cache_key(
            location_obj.code or '',
            location_obj.location_type or '',
            location_obj.name or '')
        self.cache[cache_key] = location_obj

def map_attribute(location_type, attribute):
    slug = slugify(location_type.name, separator='_').lower()
    return '{}_{}'.format(slug, attribute.lower())

def update_locations(df, mapping, event):
    cache = LocationCache()
    location_types = services.location_types.find().order_by('ancestor_count')

    for idx in df.index:
        for lt in location_types:
            location_code = df.ix[idx].get(map_attribute(lt, 'code'), '')
            location_name = df.ix[idx].get(map_attribute(lt, 'name'))
            location_pcode = df.ix[idx].get(map_attribute(lt, 'pcode')) \
                if lt.has_political_code else None
            location_rv = df.ix[idx].get(map_attribute(lt, 'rv')) \
                if lt.has_registered_voters else None
            location_type = lt.name.lower()

            # if the location_name attribute has no value, then skip it
            if not location_name:
                continue

            # if we have the location in the cache, then continue
            if cache.has(location_code, location_type, location_name):
                continue

            kwargs = {
                'name': location_name,
                'location_type': lt.name,
                'deployment': event.deployment
            }
            if location_code:
                kwargs.update({'code': location_code})
            if location_pcode:
                kwargs.update({'political_code': location_pcode})
            if location_rv:
                kwargs.update({'registered_voters': location_rv})

            location = services.locations.get_or_create(**kwargs)

            location.update(set__ancestors_ref=[])

            # update ancestors
            ancestors = []
            for sub_lt in lt.ancestors_ref:
                sub_lt_name = df.ix[idx].get(map_attribute(sub_lt, 'name'))
                sub_lt_code = df.ix[idx].get(map_attribute(sub_lt, 'code'))
                sub_lt_type = sub_lt.name.lower()

                ancestor = cache.get(sub_lt_code, sub_lt_type, sub_lt_name)
                ancestors.append(ancestor)

            location.update(
                add_to_set__events=event,
                add_to_set__ancestors_ref=ancestors)
            cache.set(location)


@celery.task
def import_locations(upload_id, mappings):
    upload = services.user_uploads.get(pk=upload_id)
    dataframe = helpers.load_source_file(upload.data)

    update_locations(
        dataframe,
        upload.event,
        mappings
    )

    # delete uploaded file
    upload.data.delete()
    upload.delete()

    msg_body = render_template_string(
        email_template
    )

    send_email(_('Locations Import Report'), msg_body, [upload.user.email])
