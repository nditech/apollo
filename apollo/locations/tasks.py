from hashlib import sha256
import pandas as pd
from .. import services


class LocationCache():
    cache = {}

    def _cache_key(self, location_type, location_name):
        # remove smart quotes
        location_type = location_type.replace(
            u"\u2018", "").replace(
            u"\u2019", "").replace(u"\u201c", "").replace(u"\u201d", "")
        location_name = location_name.replace(
            u"\u2018", "").replace(
            u"\u2019", "").replace(u"\u201c", "").replace(u"\u201d", "")
        return sha256(
            '{}:{}'.format(location_type, location_name)).hexdigest()

    def get(self, location_type, location_name):
        cache_key = self._cache_key(location_type, location_name)
        return self.cache.get(cache_key, None)

    def has(self, location_type, location_name):
        cache_key = self._cache_key(location_type, location_name)
        return cache_key in self.cache

    def set(self, location_obj):
        cache_key = self._cache_key(
            location_obj.location_type, location_obj.name)
        self.cache[cache_key] = location_obj


def location_kwargs(item, df_series):
    mapping_item = item.copy()
    items_to_pop = []
    for key in mapping_item:
        if mapping_item[key]:
            if callable(mapping_item[key]):
                mapping_item[key] = mapping_item[key](df_series)
            else:
                mapping_item[key] = df_series.get(mapping_item[key])
        else:
            items_to_pop.append(key)
    map(lambda item: mapping_item.pop(item), items_to_pop)
    return mapping_item


def update_locations(fh, mapping, event):
    cache = LocationCache()

    df = pd.read_excel(fh, 0).fillna('')

    for idx in df.index:
        for lt in mapping.keys():
            if not cache.has(lt, df.ix[idx][mapping[lt]['name']]):
                kwargs = location_kwargs(mapping[lt], df.ix[idx])
                kwargs['location_type'] = lt
                kwargs['deployment'] = event.deployment
                loc = services.locations.get_or_create(**kwargs)
                cache.set(loc)
        for lt in mapping.keys():
            loc = cache.get(lt, df.ix[idx][mapping[lt]['name']])
            ancestor_types = services.location_types.get(name=lt).ancestors_ref
            anc = filter(
                lambda a: a is not None,
                [cache.get(lt.name, df.ix[idx][mapping[lt.name]['name']])
                 for lt in ancestor_types])
            loc.ancestors_ref = anc
            loc.events.append(event)
            loc.save()
