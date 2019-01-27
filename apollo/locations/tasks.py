# -*- coding: utf-8 -*-
import cachetools
from hashlib import sha256
import logging
import os

from flask import render_template_string
from flask_babelex import lazy_gettext as _
from pandas import isnull
from slugify import slugify
from sqlalchemy import func

from apollo import helpers
from apollo.core import db, uploads
from apollo.factory import create_celery_app
from apollo.locations import utils
from apollo.messaging.tasks import send_email

from .models import LocationSet
from .models import Location, LocationPath, LocationType, LocationTypePath
from ..users.models import UserUpload

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

        plain_key = f'{location_code}:{location_type}:{location_name}'
        return sha256(plain_key.encode('utf-8')).hexdigest()

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


def update_locations(data_frame, header_mapping, location_set, task):
    cache = LocationCache()
    locales = location_set.deployment.locale_codes

    num_records = data_frame.shape[0]
    processed_records = 0
    error_records = 0

    location_types = LocationType.query.filter(
        LocationType.location_set == location_set).join(
            LocationTypePath,
            LocationType.id == LocationTypePath.ancestor_id).order_by(
                func.count(LocationType.ancestor_paths)).group_by('id').all()

    all_loc_type_paths = LocationTypePath.query.with_entities(
        LocationTypePath.ancestor_id,
        LocationTypePath.descendant_id,
        LocationTypePath.depth).all()

    extra_field_cache = {
        fi.id: fi.name for fi in location_set.extra_fields
    } if location_set.extra_fields else {}

    for idx in data_frame.index:
        current_row = data_frame.ix[idx]
        row_ids = {}
        for loc_type in location_types:
            name_column_keys = [
                f'{loc_type.id}_name_{locale}'
                for locale in locales
            ]
            code_column_key = '{}_code'.format(loc_type.id)

            if (
                header_mapping.get(name_column_keys[0]) is None or
                header_mapping.get(code_column_key) is None
            ):
                error_records += 1
                continue

            lat_column_key = '{}_lat'.format(loc_type.id)
            lon_column_key = '{}_lon'.format(loc_type.id)
            reg_voters_column_key = '{}_rv'.format(loc_type.id) \
                if loc_type.has_registered_voters else None

            name_columns = [
                header_mapping.get(col) for col in name_column_keys]
            code_column = header_mapping.get(code_column_key)
            lat_column = header_mapping.get(lat_column_key)
            lon_column = header_mapping.get(lon_column_key)
            reg_voters_column = header_mapping.get(reg_voters_column_key)

            location_names = [current_row.get(col) for col in name_columns]
            location_code = current_row.get(code_column)
            if isinstance(location_code, (int, float)):
                location_code = str(int(location_code))

            # skip if we're missing a name or code
            if not location_names[0] or not location_code:
                error_records += 1
                continue

            location_lat = None
            location_lon = None
            location_rv = None

            location_lat = current_row.get(lat_column)
            location_lon = current_row.get(lon_column)
            location_rv = current_row.get(reg_voters_column)

            try:
                location_lat = float(location_lat)
                location_lon = float(location_lon)
            except (TypeError, ValueError):
                location_lat = location_lon = None

            try:
                if loc_type.has_registered_voters:
                    location_rv = int(location_rv)
            except (TypeError, ValueError):
                location_rv = None

            # if we have the location in the cache, then continue
            if cache.has(location_code, loc_type, location_names[0]):
                loc = cache.get(location_code, loc_type, location_names[0])
                row_ids[loc_type.id] = loc.id
                continue

            kwargs = {
                'location_type_id': loc_type.id,
                'location_set_id': location_set.id,
                'lat': location_lat,
                'lon': location_lon,
                'code': location_code,
                'name_translations': {
                    locale: name
                    for locale, name in zip(locales, location_names) if name
                }
            }

            if location_rv:
                kwargs.update({'registered_voters': location_rv})

            # is this location in the database?
            location = Location.query.filter(
                Location.location_set == location_set,
                Location.code == kwargs['code']).first()

            if not location:
                # no, create it
                location = Location.create(**kwargs)
                location.save()

                # also add the self-referencing path
                self_ref_path = LocationPath(
                    location_set_id=location_set.id, ancestor_id=location.id,
                    descendant_id=location.id, depth=0)

                db.session.add(self_ref_path)
                db.session.commit()
            else:
                # update the existing location instead
                location.name_translations = kwargs.get('name_translations')
                location.registered_voters = kwargs.get('registered_voters')
                location.lat = kwargs.get('lat')
                location.lon = kwargs.get('lon')

                location.save()

            # each level should have its own extra data column
            extra_data = {}
            for field_id in extra_field_cache.keys():
                column_key = '{}:{}'.format(loc_type.id, field_id)
                column = header_mapping.get(column_key)
                if column:
                    value = current_row.get(column)
                    if isnull(value):
                        continue
                    extra_data[extra_field_cache[field_id]] = value

            if extra_data:
                Location.query.filter(Location.id == location.id).update(
                    {'extra_data': extra_data}, synchronize_session=False)

            row_ids[loc_type.id] = location.id
            cache.set(location)

        for ancestor_lt_id, descendant_lt_id, depth in all_loc_type_paths:
            if ancestor_lt_id == descendant_lt_id:
                continue

            ancestor_loc_id = row_ids.get(ancestor_lt_id)
            descendant_loc_id = row_ids.get(descendant_lt_id)

            if not descendant_loc_id:
                # TODO: a missing ancestor_id is evil that should
                # never be tolerated
                continue

            path = LocationPath.query.filter_by(
                ancestor_id=ancestor_loc_id,
                descendant_id=descendant_loc_id,
                depth=depth
            ).first()

            if not path:
                path = LocationPath(
                    ancestor_id=ancestor_loc_id,
                    descendant_id=descendant_loc_id,
                    location_set_id=location_set.id,
                    depth=depth
                )

                db.session.add(path)

            db.session.commit()

        processed_records += 1

        task.update_progress(**{
            'num_records': num_records,
            'processed_records': processed_records,
            'error_records': error_records
        })


@celery.task(bind=True)
def import_locations(self, upload_id, mappings, location_set_id):
    upload = UserUpload.query.filter(UserUpload.id == upload_id).first()
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

    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first()

    update_locations(
        dataframe,
        mappings,
        location_set,
        self
    )

    os.remove(filepath)
    upload.delete()

    msg_body = render_template_string(
        email_template
    )

    send_email(_('Locations Import Report'), msg_body, [upload.user.email])

    return self.progress


@celery.task
def nuke_locations(location_set_id):
    utils.nuke_locations(location_set_id)
