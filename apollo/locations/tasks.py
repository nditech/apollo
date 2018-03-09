# -*- coding: utf-8 -*-
import cachetools
from hashlib import sha256
import logging
import os

from flask import render_template_string
from flask_babelex import lazy_gettext as _
from slugify import slugify
from sqlalchemy import func

from apollo import helpers, models, services
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
            location_set=location_set) \
        .join(models.LocationTypePath,
              models.LocationType.id == models.LocationTypePath.ancestor_id) \
        .order_by(func.count(models.LocationType.ancestor_paths)) \
        .group_by('id').all()
    # depth = [p.depth for p in location_types[-1].ancestor_paths]

    # basically, all the info required for linking is (supposedly)
    # already in the db. so just use it to start creating the links
    all_lt_paths = models.LocationTypePath.query.with_entities(
        models.LocationTypePath.ancestor_id,
        models.LocationTypePath.descendant_id,
        models.LocationTypePath.depth,
    ).all()

    for idx in df.index:
        # row_locations = []
        row_ids = {}

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
            # same for the location_code
            if not location_name or not location_code:
                continue

            # if we have the location in the cache, then continue
            if cache.has(location_code, location_type, location_name):
                loc = cache.get(location_code, location_type, location_name)
                row_ids[lt.id] = loc.id
                continue

            kwargs = {
                'location_type_id': lt.id,
                'deployment_id': lt.deployment.id,
                'location_set_id': location_set.id
            }

            kwargs.update({'code': location_code})

            kwargs['name'] = location_name

            if location_pcode:
                kwargs.update({'political_code': location_pcode})
            if location_ocode:
                kwargs.update({'other_code': location_ocode})
            if location_rv:
                kwargs.update({'registered_voters': location_rv})

            # skip if we have the location in the database
            location = services.locations.find(
                deployment=lt.deployment, location_set=location_set,
                code=kwargs['code']).first()

            if not location:
                location = services.locations.create(**kwargs)

                # also add the self-referencing path
                self_ref_path = models.LocationPath(
                    location_set_id=location_set.id, ancestor_id=location.id,
                    descendant_id=location.id, depth=0)

                db.session.add(self_ref_path)
                db.session.commit()
            else:
                # update the existing location instead

                location.name = kwargs.get('name')
                location.other_code = kwargs.get('other_code')
                location.political_code = kwargs.get('political_code')
                location.registered_voters = kwargs.get('registered_voters')

                location.save()

            # row_locations.append(location)
            row_ids[lt.id] = location.id
            cache.set(location)

        for ancestor_lt_id, descendant_lt_id, depth in all_lt_paths:
            if ancestor_lt_id == descendant_lt_id:
                continue

            ancestor_loc_id = row_ids.get(ancestor_lt_id)
            descendant_loc_id = row_ids.get(descendant_lt_id)

            if not descendant_loc_id:
                # TODO: a missing ancestor_id is evil that should
                # never be tolerated
                continue

            path = models.LocationPath.query.filter_by(
                ancestor_id=ancestor_loc_id,
                descendant_id=descendant_loc_id,
                depth=depth
            ).first()

            if not path:
                path = models.LocationPath(
                    ancestor_id=ancestor_loc_id,
                    descendant_id=descendant_loc_id,
                    location_set_id=location_set.id,
                    depth=depth
                )

                db.session.add(path)

            db.session.commit()


@celery.task
def import_locations(upload_id, mappings, location_set_id):
    upload = services.user_uploads.find(id=upload_id).first()
    if not upload:
        logger.error('Upload %s does not exist, aborting', upload_id)
        return

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

    os.remove(filepath)
    upload.delete()

    msg_body = render_template_string(
        email_template
    )

    send_email(_('Locations Import Report'), msg_body, [upload.user.email])


@celery.task
def nuke_locations(location_set_id):
    utils.nuke_locations(location_set_id)
