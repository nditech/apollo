# -*- coding: utf-8 -*-
import cachetools
from hashlib import sha256
import logging
import os

from flask import render_template_string
from flask_babelex import lazy_gettext as _
from slugify import slugify

from apollo import helpers, services
from apollo.core import db, uploads
from apollo.factory import create_celery_app
from apollo.locations import utils
from apollo.messaging.tasks import send_email

celery = create_celery_app()
logger = logging.getLogger(__name__)

email_template = '''
Notification
------------

Your location import task has been completed.
'''


class LocationCache():
    cache = cachetools.LRUCache(maxsize=50)

    def _cache_key(self, location_code, location_type, location_name):
        # remove smart quotes
        location_code = str(location_code).replace(
            "\u2018", "").replace(
            "\u2019", "").replace("\u201c", "").replace("\u201d", "")
        location_type = str(location_type).replace(
            "\u2018", "").replace(
            "\u2019", "").replace("\u201c", "").replace("\u201d", "")
        location_name = str(location_name).replace(
            "\u2018", "").replace(
            "\u2019", "").replace("\u201c", "").replace("\u201d", "")
        return sha256(
            '{}:{}:{}'.format(
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
            location_obj.location_type.name or '',
            location_obj.name or '')
        self.cache[cache_key] = location_obj


def map_attribute(location_type, attribute):
    slug = slugify(location_type.name, separator='_').lower()
    return '{}_{}'.format(slug, attribute.lower())


def update_locations(df, mapping, location_set):
    cache = LocationCache()
    location_types = services.location_types.find(
        deployment=location_set.deployment,
        location_set=location_set)

    for idx in df.index:
        for lt in location_types:
            location_code = df.ix[idx].get(mapping.get(map_attribute(lt, 'code'), ''), '')
            location_code = int(location_code) if type(location_code) in [int, float] else location_code
            location_code = str(location_code)
            location_name = str(df.ix[idx].get(
                mapping.get(map_attribute(lt, 'name'), ''),
                ''
            ))
            location_pcode = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'pcode'), ''), '') \
                if lt.has_political_code else None
            location_ocode = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'ocode'), ''), '') \
                if lt.has_other_code else None
            if location_pcode:
                location_pcode = int(location_pcode) if type(location_pcode) in [int, float] else location_pcode
                location_pcode = str(location_pcode)
            if location_ocode:
                location_ocode = int(location_ocode) if type(location_ocode) in [int, float] else location_ocode
                location_ocode = str(location_ocode)
            location_rv = df.ix[idx].get(
                mapping.get(map_attribute(lt, 'rv'), ''), '') \
                if lt.has_registered_voters else None
            if location_rv:
                location_rv = int(location_rv) if type(location_rv) in [int, float] else location_rv
            location_type = lt

            # if the location_name attribute has no value, then skip it
            if not location_name:
                continue

            # if we have the location in the cache, then continue
            if cache.has(location_code, location_type, location_name):
                continue

            kwargs = {
                'location_type_id': lt.id,
                'deployment_id': lt.deployment.id,
                'location_set_id': location_set.id
            }

            if location_code:
                kwargs.update({'code': location_code})

            # location = services.locations.get_or_create(**kwargs)
            # location_data = dict()

            kwargs['name'] = location_name

            if location_pcode:
                kwargs.update({'political_code': location_pcode})
            if location_ocode:
                kwargs.update({'other_code': location_ocode})
            if location_rv:
                kwargs.update({'registered_voters': location_rv})

            # update = dict(
            #     [('set__{}'.format(k), v)
            #      for k, v in list(location_data.items())]
            # )

            # location.update(set__ancestors_ref=[], **update)
            # location.reload()

            # skip if we have the location in the database
            location = services.locations.find(
                deployment=lt.deployment, location_set=location_set,
                code=kwargs['code']).first()
            if not location:
                location = services.locations.create(**kwargs)

            # update ancestors
            # ancestors = []
            # for sub_lt in lt.ancestors():
            #     sub_lt_name = str(df.ix[idx].get(
            #         mapping.get(map_attribute(sub_lt, 'name'), '')))
            #     sub_lt_code = df.ix[idx].get(
            #         mapping.get(map_attribute(sub_lt, 'code'), ''), '')
            #     sub_lt_code = int(sub_lt_code) if type(sub_lt_code) in [int, float] else sub_lt_code
            #     sub_lt_code = str(sub_lt_code)
            #     sub_lt_type = sub_lt.name or ''

            #     ancestor = cache.get(sub_lt_code, sub_lt_type, sub_lt_name)
            #     if not ancestor:
            #         ancestor = services.locations.find(
            #             deployment=lt.deployment, code=sub_lt_code,
            #             location_type=sub_lt, location_set=location_set,
            #             name=sub_lt_name)
            #     if ancestor:
            #         ancestors.append(ancestor)

            # for ancestor in ancestors:
            #     path = models.LocationPath(
            #         location_set_id=location_set.id, ance)
            cache.set(location)


@celery.task
def import_locations(upload_id, mappings, location_set_id):
    upload = services.user_uploads.find(id=upload_id).first()
    filepath = uploads.path(upload.upload_filename)

    if not os.path.exists(filepath):
        logger.error('Upload file %s does not exist, aborting', filepath)
        upload.delete()
        return

    with open(filepath) as f:
        dataframe = helpers.load_source_file(f)

    location_set = services.location_sets.find(
        id=location_set_id).first()

    update_locations(
        dataframe,
        mappings,
        location_set
    )

    # fetch and update all submissions
    # deployment = upload.event.deployment
    # submissions = services.submissions.all().filter(deployment=deployment)
    # for submission in submissions:
    #     if submission.location:
    #         submission.location_name_path = helpers.compute_location_path(submission.location)
    #         submission.save(clean=False)

    # delete uploaded file
    os.remove(filepath)
    upload.delete()

    msg_body = render_template_string(
        email_template
    )

    send_email(_('Locations Import Report'), msg_body, [upload.user.email])


@celery.task
def nuke_locations():
    utils.nuke_locations()
