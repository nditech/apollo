# -*- coding: utf-8 -*-
import cachetools
from hashlib import sha256
import logging
import numbers
import os

from flask import render_template_string
from flask_babelex import gettext
from flask_babelex import lazy_gettext as _
from pandas import isnull
from slugify import slugify
from sqlalchemy import and_, exists, func
from sqlalchemy.sql import select

from apollo import helpers
from apollo.core import db, uploads
from apollo.factory import create_celery_app
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

    def set_by_dict(self, **data):
        cache_key = self._cache_key(
            data.get('code', ''),
            data.get('loc_type_name', ''),
            data.get('name', '')
        )
        self.cache[cache_key] = data.get('id')


def map_attribute(location_type, attribute):
    slug = slugify(location_type.name, separator='_').lower()
    return '{}_{}'.format(slug, attribute.lower())


def update_locations(
        connection, data_frame, header_mapping, location_set, task):
    cache = LocationCache()

    mapped_locales = [
        k.rsplit('_', 1)[-1] for k in header_mapping.keys() if 'name' in k]

    total_records = data_frame.shape[0]
    processed_records = 0
    error_records = 0
    warning_records = 0
    total_locations = 0
    error_log = []

    mapped_location_type_ids = [
        int(k[:-5]) for k in header_mapping.keys() if k.endswith('_code')]

    location_types = LocationType.query.filter(
        LocationType.location_set == location_set,
        LocationType.id.in_(mapped_location_type_ids)
    ).join(
        LocationTypePath,
        LocationType.id == LocationTypePath.ancestor_id
    ).order_by(
        func.count(LocationType.ancestor_paths).desc()
    ).group_by('id').all()

    all_loc_type_paths = LocationTypePath.query.filter_by(
        location_set_id=location_set.id
    ).with_entities(
        LocationTypePath.ancestor_id,
        LocationTypePath.descendant_id,
        LocationTypePath.depth
    ).all()

    extra_field_cache = {
        fi.id: fi.name for fi in location_set.extra_fields
    } if location_set.extra_fields else {}

    location_table = Location.__table__
    location_path_table = LocationPath.__table__

    # due to the way the reports are presented, one only wants to report
    # (counts of) errors/warnings once per row of data, even if multiple
    # issues arise per row, since there's no way to enforce a specific
    # spreadsheet structure

    for idx in data_frame.index:
        current_row = data_frame.ix[idx]
        location_path_helper_map = {}
        error_this_row = False
        warning_this_row = False

        for loc_type in location_types:
            name_column_keys = [
                f'{loc_type.id}_name_{locale}' for locale in mapped_locales]
            code_column_key = f'{loc_type.id}_code'

            if (
                header_mapping.get(name_column_keys[0]) is None or
                header_mapping.get(code_column_key) is None
            ):
                warning_records += (0 if warning_this_row else 1)
                error_log.append({
                    'label': 'WARNING',
                    'message': gettext(
                        'No code or name present for row %(row)d for %(level)s',
                        row=(idx + 1), level=loc_type.name)
                })
                warning_this_row = True
                continue

            lat_column_key = f'{loc_type.id}_lat' \
                if loc_type.has_coordinates else None
            lon_column_key = f'{loc_type.id}_lon' \
                if loc_type.has_coordinates else None
            reg_voters_column_key = f'{loc_type.id}_rv' \
                if loc_type.has_registered_voters else None

            name_columns = [
                header_mapping.get(col) for col in name_column_keys]
            code_column = header_mapping.get(code_column_key)
            lat_column = header_mapping.get(lat_column_key)
            lon_column = header_mapping.get(lon_column_key)
            reg_voters_column = header_mapping.get(reg_voters_column_key)

            location_names = [current_row.get(col) for col in name_columns]
            location_code = current_row.get(code_column)

            # sanity check because numeric 0 is (probably) a valid code
            # but is a falsy value
            if location_code == 0:
                location_code = str(location_code)

            if not location_names[0] and not location_code:
                # the other columns are likely blank
                continue

            try:
                location_code = str(int(location_code))
            except (TypeError, ValueError):
                error_records += (0 if error_this_row else 1)
                message = gettext(
                    'Invalid (non-numeric) location code (%(loc_code)s)',
                    loc_code=location_code)
                error_log.append({
                    'label': 'ERROR',
                    'message': message
                })
                error_this_row = True
                continue

            # it's an issue if either is missing, too
            if not location_names[0] or not location_code:
                warning_records += (0 if warning_this_row else 1)
                error_log.append({
                    'label': 'WARNING',
                    'message': gettext(
                        'Missing name or code for row %(row)d',
                        row=(idx + 1)
                    )
                })
                warning_this_row = True
                continue

            # if we have the location in the cache, then continue
            if cache.has(location_code, loc_type.name, location_names[0]):
                location_path_helper_map[loc_type.id] = cache.get(
                    location_code, loc_type.name, location_names[0])
                continue

            location_lat = current_row.get(lat_column)
            location_lon = current_row.get(lon_column)
            location_rv = current_row.get(reg_voters_column)

            if loc_type.has_coordinates:
                try:
                    location_lat = float(location_lat)
                    location_lon = float(location_lon)
                except (TypeError, ValueError):
                    warning_records += (0 if warning_this_row else 1)
                    error_log.append({
                        'label': 'WARNING',
                        'message': gettext('Invalid coordinate data for row %(row)d. Data will not be used.', row=(idx + 1))
                    })
                    location_lat = location_lon = None
                    warning_this_row = True
            else:
                location_lat = location_lon = None

            if loc_type.has_registered_voters:
                try:
                    location_rv = int(location_rv)
                except (TypeError, ValueError):
                    warning_records += (0 if warning_this_row else 1)
                    error_log.append({
                        'label': 'WARNING',
                        'message': gettext('Invalid number of registered voters for row %(row)d. Data will not be used.', row=(idx + 1))
                    })
                    location_rv = None
                    warning_this_row = True
            else:
                location_rv = 0

            # set GPS data if we have valid data
            if location_lat is not None and location_lon is not None:
                geom_spec = 'SRID=4326; POINT({longitude:f} {latitude:f})'.format(  # noqa
                    longitude=location_lon, latitude=location_lat)
            else:
                geom_spec = None

            # each level should have its own extra data column
            extra_data = {}
            for field_id in extra_field_cache.keys():
                column_key = '{}:{}'.format(loc_type.id, field_id)
                column = header_mapping.get(column_key)
                if column:
                    value = current_row.get(column)
                    if isnull(value):
                        continue
                    if isinstance(value, numbers.Number):
                        if isinstance(value, numbers.Integral):
                            value = int(value)
                        else:
                            value = float(value)
                    else:
                        value = str(value)
                    extra_data[extra_field_cache[field_id]] = value

            # collate all fields
            kwargs = {
                'location_type_id': loc_type.id,
                'location_set_id': location_set.id,
                'geom': geom_spec,
                'code': location_code,
                'name_translations': {
                    locale: str(name).strip()
                    for locale, name in zip(
                        mapped_locales, location_names
                    ) if name and not isnull(name)
                }
            }
            if location_rv:
                kwargs.update({'registered_voters': location_rv})
            if extra_data:
                kwargs.update({'extra_data': extra_data})

            # is this location in the database?
            s = select([location_table.c.id]).where(and_(
                location_table.c.location_set_id == location_set.id,
                location_table.c.code == kwargs['code']
            ))
            with connection.begin():
                result = connection.execute(s)
                location_data = result.first()

            # create it if it isn't
            if location_data is None:
                stmt = location_table.insert().values(**kwargs)
                with connection.begin():
                    result = connection.execute(stmt)
                    location_id = result.inserted_primary_key[0]
                    result.close()

                # add the self-referential path
                stmt = location_path_table.insert().values(
                    ancestor_id=location_id, descendant_id=location_id,
                    location_set_id=location_set.id, depth=0
                )
                with connection.begin():
                    result = connection.execute(stmt)
                    result.close()
            else:
                # update it if it is
                location_id = location_data[0]
                update_kwargs = {
                    'registered_voters': kwargs.get('registered_voters'),
                    'name_translations': kwargs.get('name_translations'),
                    'geom': kwargs.get('geom'),
                }
                if extra_data:
                    update_kwargs['extra_data'] = extra_data

                stmt = location_table.update().where(
                    location_table.c.id == location_id
                ).values(**update_kwargs)

                with connection.begin():
                    connection.execute(stmt)

            total_locations += 1
            cache.set_by_dict(
                loc_type_name=loc_type.name, code=location_code,
                name=location_names[0], id=location_id)

            # update location path info for this row
            location_path_helper_map[loc_type.id] = location_id

        for ans_type_id, des_type_id, depth in all_loc_type_paths:
            ancestor_id = location_path_helper_map.get(ans_type_id)
            descendant_id = location_path_helper_map.get(des_type_id)
            path_result = None

            if ancestor_id is None or descendant_id is None:
                continue

            with connection.begin():
                stmt = exists().where(and_(
                    location_path_table.c.ancestor_id == ancestor_id,
                    location_path_table.c.descendant_id == descendant_id,
                    location_path_table.c.location_set_id == location_set.id
                )).select()
                path_result = connection.execute(stmt).scalar()

            if not path_result:
                stmt = location_path_table.insert().values(
                    ancestor_id=ancestor_id, descendant_id=descendant_id,
                    location_set_id=location_set.id, depth=depth
                )
                with connection.begin():
                    result = connection.execute(stmt)
                    result.close()

        processed_records += 1
        task.update_task_info(
            total_records=total_records,
            processed_records=processed_records,
            error_records=error_records,
            warning_records=warning_records,
            error_log=error_log
        )


@celery.task(bind=True)
def import_locations(self, upload_id, mappings, location_set_id, channel=None):
    upload = UserUpload.query.filter(UserUpload.id == upload_id).first()
    if not upload:
        logger.error('Upload %s does not exist, aborting', upload_id)
        return

    filepath = uploads.path(upload.upload_filename)

    if not os.path.exists(filepath):
        logger.error('Upload file %s does not exist, aborting', filepath)
        upload.delete()
        return

    with open(filepath, 'rb') as f:
        dataframe = helpers.load_source_file(f)

    location_set = LocationSet.query.filter(
        LocationSet.id == location_set_id).first()

    engine = db.session.get_bind()
    with engine.begin() as connection:
        update_locations(
            connection,
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
