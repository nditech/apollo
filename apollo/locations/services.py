# -*- coding: utf-8 -*-
import csv
from io import StringIO

from apollo import constants
from apollo.dal.service import Service
from apollo.locations.models import Location, LocationSet, LocationType, Sample


class LocationSetService(Service):
    __model__ = LocationSet


class LocationService(Service):
    __model__ = Location

    def export_list(self, query):
        headers = []
        location_set = query.first().location_set
        location_types = LocationTypeService().find(
            location_set_id=location_set.id
        ).join()

        locales = location_set.deployment.locale_codes

        for location_type in location_types:
            location_type_name = location_type.name.upper()
            type_locale_headers = [
                f'{location_type_name}_N_{locale.upper()}'
                for locale in locales
            ]
            headers.extend(type_locale_headers)
            headers.append('{}_ID'.format(location_type_name))
            if location_type.has_registered_voters:
                headers.append('{}_RV'.format(location_type_name))

        output = StringIO()
        output.write(constants.BOM_UTF8_STR)
        writer = csv.writer(output)
        writer.writerow(headers)
        yield output.getvalue()
        output.close()

        locations = query.order_by('code')
        for location in locations:
            record = []
            ancestors = location.ancestors()
            for ancestor in ancestors:
                for locale in locales:
                    record.append(ancestor.name_translations.get(locale))
                record.append(ancestor.code)

                if ancestor.location_type.has_registered_voters:
                    record.append(ancestor.registered_voters)

            for locale in locales:
                record.append(location.name_translations.get(locale))
            record.append(location.code)

            if location.location_type.has_registered_voters:
                record.append(location.registered_voters)

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(record)
            yield output.getvalue()
            output.close()

    def root(self, location_set_id):
        return self.__model__.root(location_set_id)


class LocationTypeService(Service):
    __model__ = LocationType

    def root(self, location_set_id):
        return self.__model__.root(location_set_id)


class SampleService(Service):
    __model__ = Sample
