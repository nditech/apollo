from apollo.core import Service, cache
from apollo.locations.models import Sample, LocationType, Location
import unicodecsv
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class SamplesService(Service):
    __model__ = Sample


class LocationTypesService(Service):
    __model__ = LocationType

    def root(self):
        # a raw query is needed because querying 'normally'
        # (i.e.: ancestors_ref=[]) will raise an exception
        # about an invalid ObjectID
        return self.find(__raw__={'ancestors_ref': []}).first()


class LocationsService(Service):
    __model__ = Location

    def root(self):
        # a raw query is needed because querying 'normally'
        # (i.e.: ancestors_ref=[]) will raise an exception
        # about an invalid ObjectID
        return self.find(__raw__={'ancestors_ref': []}).first()

    @cache.memoize(timeout=86400)
    def registered_voters_map(self):
        '''
        This method computes a map of location ids and the corresponding
        number of registered voters and cache the result for a day.
        '''
        eligible_location_types = LocationTypesService().find(
            has_registered_voters=True).scalar('name')
        return {pk: rv for (pk, rv) in self.find(
            location_type__in=eligible_location_types).scalar(
            'pk', 'registered_voters')}

    def export_list(self, queryset):
        headers = []
        location_types = list(LocationTypesService().find().order_by(
            'ancestors_ref'))
        for location_type in location_types:
            location_name = location_type.name.upper()
            headers.append('{}_N'.format(location_name))
            headers.append('{}_ID'.format(location_name))
            if location_type.has_political_code:
                headers.append('{}_PCODE'.format(location_name))
            if location_type.has_registered_voters:
                headers.append('{}_RV'.format(location_name))
            for metafield in location_type.metafields:
                headers.append('{}_{}'.format(
                    location_name, metafield.upper()
                ))

        output = StringIO()
        writer = unicodecsv.writer(output, encoding='utf-8')
        writer.writerow([unicode(i) for i in headers])
        yield output.getvalue()
        output.close()

        if queryset.count() < 1:
            yield
        else:
            locations = queryset
            locations = locations.order_by('code')
            for location in locations:
                record = []
                for location_type in location_types:
                    try:
                        this_location = filter(
                            lambda l: l.location_type == location_type.name,
                            location.ancestors_ref
                        ).pop()
                    except IndexError:
                        if location.location_type == location_type.name:
                            this_location = location
                        else:
                            this_location = None
                    record.append(this_location.name or ''
                                  if this_location else '')
                    record.append(this_location.code or ''
                                  if this_location else '')
                    if location_type.has_political_code:
                        record.append(this_location.political_code or ''
                                      if this_location else '')
                    if location_type.has_registered_voters:
                        record.append(this_location.registered_voters or ''
                                      if this_location else '')
                    for metafield in location_type.metafields:
                        record.append(getattr(this_location, metafield, '')
                                      if this_location else '')

                output = StringIO()
                writer = unicodecsv.writer(output, encoding='utf-8')
                writer.writerow([unicode(i) for i in record])
                yield output.getvalue()
                output.close()
