from hashlib import sha256

import pandas as pd

from .. import helpers, services
from ..factory import create_celery_app

celery = create_celery_app()

email_template = '''
Of {{ count }} records, {{ successful_imports }} were successfully imported, {{ suspect_imports }} raised warnings, and {{ unsuccessful_imports }} could not be imported.
{% if errors %}
The following records could not be imported:
-------------------------
{% for e in errors %}
{%- set pid = e[0] %}{% set msg = e[1] -%}
Record for Location ID {{ pid }} raised error: {{ msg }}
{% endfor %}
{% endif %}

{% if warnings %}
The following records raised warnings:
{% for e in warnings %}
{%- set pid = e[0] %}{% set msg = e[1] -%}
Record for Location ID {{ pid }} raised warning: {{ msg }}
{% endfor %}
{% endif %}
'''

field_transform = {
    'code': lambda s: str(s),
    'political_code': lambda s: str(s),
    'registered_voters': lambda i: int(i)
}


class LocationCache():
    cache = {}

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


def location_kwargs(item, df_series):
    mapping_item = item.copy()
    items_to_pop = []
    for key in mapping_item:
        if mapping_item[key]:
            if key in field_transform:
                mapping_item[key] = field_transform.get(key)(
                    df_series.get(mapping_item[key]))
            else:
                mapping_item[key] = df_series.get(mapping_item[key])
        else:
            items_to_pop.append(key)
    map(lambda item: mapping_item.pop(item), items_to_pop)
    return mapping_item


def update_locations(df, mapping, event):
    cache = LocationCache()

    for idx in df.index:
        for lt in mapping.keys():
            if not cache.has(
                df.ix[idx][mapping[lt]['code']] if mapping[lt]['code'] else '',
                lt or '',
                df.ix[idx][mapping[lt]['name']] if mapping[lt]['name'] else ''
            ):
                kwargs = location_kwargs(mapping[lt], df.ix[idx])
                kwargs['location_type'] = lt
                kwargs['deployment'] = event.deployment
                loc = services.locations.get_or_create(**kwargs)
                cache.set(loc)
        for lt in mapping.keys():
            loc = cache.get(
                df.ix[idx][mapping[lt]['code']] if mapping[lt]['code'] else '',
                lt or '',
                df.ix[idx][mapping[lt]['name']] if mapping[lt]['name'] else '')
            ancestor_types = services.location_types.get(name=lt).ancestors_ref
            anc = filter(
                lambda a: a, [cache.get(
                    df.ix[idx][mapping[lt.name]['code']]
                    if mapping[lt.name]['code'] else '',
                    lt.name or '',
                    df.ix[idx][mapping[lt.name]['name']]
                    if mapping[lt.name]['name'] else '')
                    for lt in ancestor_types])
            loc.update(add_to_set__events=event, add_to_set__ancestors_ref=anc)


@celery.task
def import_locations(upload_id, mappings):
    upload = services.user_uploads.get(pk=upload_id)
    dataframe = helpers.load_source_file(upload.data)
    count, errors, warnings = update_locations(
        dataframe,
        upload.event,
        mappings
    )

    # delete uploaded file
    upload.data.delete()
    upload.delete()

    msg_body = generate_response_email(count, errors, warnings)

    send_email(_('Import report'), msg_body, [upload.user.email])
