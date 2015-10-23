import cachetools
from flask import render_template_string
from flask.ext.babel import lazy_gettext as _
from hashlib import sha256
from slugify import slugify

from apollo import helpers, services
from apollo.factory import create_celery_app
from apollo.messaging.tasks import send_email

celery = create_celery_app()

email_template = '''
Notification
------------

Your location import task has been completed.
'''


class LocationCache():
    cache = cachetools.LRUCache(maxsize=50)

    def _cache_key(self, location_code, location_type, location_name):
        # remove smart quotes
        location_code = unicode(location_code).replace(
            u"\u2018", u"").replace(
            u"\u2019", u"").replace(u"\u201c", u"").replace(u"\u201d", u"")
        location_type = unicode(location_type).replace(
            u"\u2018", u"").replace(
            u"\u2019", u"").replace(u"\u201c", u"").replace(u"\u201d", u"")
        location_name = unicode(location_name).replace(
            u"\u2018", u"").replace(
            u"\u2019", u"").replace(u"\u201c", u"").replace(u"\u201d", u"")
        return sha256(
            u'{}:{}:{}'.format(
                location_code, location_type, location_name).encode('utf-8')).hexdigest()

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
    return u'{}_{}'.format(slug, attribute.lower())


def update_locations(df, mapping, event):
    cache = LocationCache()
    location_types = services.location_types.all().filter(
        deployment=event.deployment).order_by('ancestor_count')

    for idx in df.index:
        for lt in location_types:
            location_code = df.ix[idx].get(mapping.get(map_attribute(lt, 'code'), u''), u'')
            location_code = int(location_code) if type(location_code) in [int, float] else location_code
            location_code = str(location_code).decode('utf-8')
            location_name = str(df.ix[idx].get(
                mapping.get(map_attribute(lt, 'name'), u''),
                u''
            )).decode('utf-8')
            location_pcode = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'pcode'), u''), u'') \
                if lt.has_political_code else None
            location_ocode = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'ocode'), u''), u'') \
                if lt.has_other_code else None
            if location_pcode:
                location_pcode = int(location_pcode) if type(location_pcode) in [int, float] else location_pcode
                location_pcode = str(location_pcode).decode('utf-8')
            if location_ocode:
                location_ocode = int(location_ocode) if type(location_ocode) in [int, float] else location_ocode
                location_ocode = str(location_ocode).decode('utf-8')
            location_rv = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'rv'), ''), '') \
                if lt.has_registered_voters else None
            if location_rv:
                location_rv = int(location_rv) if type(location_rv) in [int, float] else location_rv
            location_type = lt.name

            # if the location_name attribute has no value, then skip it
            if not location_name:
                continue

            # if we have the location in the cache, then continue
            if cache.has(location_code, location_type, location_name):
                continue

            kwargs = {
                'location_type': lt.name,
                'deployment': event.deployment
            }

            if location_code:
                kwargs.update({'code': location_code})

            location = services.locations.get_or_create(**kwargs)
            location_data = dict()

            location_data['name'] = location_name

            if location_pcode:
                location_data.update({'political_code': location_pcode})
            if location_ocode:
                location_data.update({'other_code': location_ocode})
            if location_rv:
                location_data.update({'registered_voters': location_rv})

            update = dict(
                [('set__{}'.format(k), v)
                 for k, v in location_data.items()]
            )

            location.update(set__ancestors_ref=[], **update)
            location.reload()

            # update ancestors
            ancestors = []
            for sub_lt in lt.ancestors_ref:
                sub_lt_name = str(df.ix[idx].get(
                    mapping.get(map_attribute(sub_lt, 'name'), u''))).decode('utf-8')
                sub_lt_code = df.ix[idx].get(
                    mapping.get(map_attribute(sub_lt, 'code'), u''), u'')
                sub_lt_code = int(sub_lt_code) if type(sub_lt_code) in [int, float] else sub_lt_code
                sub_lt_code = str(sub_lt_code).decode('utf-8')
                sub_lt_type = sub_lt.name or u''

                ancestor = cache.get(sub_lt_code, sub_lt_type, sub_lt_name)
                if not ancestor:
                    ancestor = services.locations.get(
                        deployment=event.deployment, code=sub_lt_code, location_type=sub_lt_type,
                        name=sub_lt_name)
                if ancestor:
                    ancestors.append(ancestor)

            location.update(
                add_to_set__events=event,
                set__ancestors_ref=ancestors,
                set__ancestor_count=len(ancestors))
            cache.set(location)


@celery.task
def import_locations(upload_id, mappings):
    upload = services.user_uploads.get(pk=upload_id)
    dataframe = helpers.load_source_file(upload.data)

    update_locations(
        dataframe,
        mappings,
        upload.event
    )

    # fetch and update all submissions
    deployment = upload.event.deployment
    submissions = services.submissions.all().filter(deployment=deployment)
    for submission in submissions:
        if submission.location:
            submission.location_name_path = helpers.compute_location_path(submission.location)
            submission.save(clean=False)

    # delete uploaded file
    upload.data.delete()
    upload.delete()

    msg_body = render_template_string(
        email_template
    )

    send_email(_('Locations Import Report'), msg_body, [upload.user.email])
