# -*- coding: utf-8 -*-
import json

from apollo.dal.serializers import ArchiveSerializer
from apollo.locations.models import (
    Location, LocationDataField, LocationPath, LocationSet, LocationType,
    LocationTypePath, Sample)


class LocationSerializer(object):
    __model__ = Location

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()
        location_type_id = LocationType.query.filter_by(
            uuid=data['location_type']).with_entities(LocationType.id).scalar()
        samples = Sample.query.filter(
            Sample.uuid.in_(data['samples'])).all()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs.pop('location_type')
        kwargs['location_set_id'] = location_set_id
        kwargs['location_type_id'] = location_type_id
        kwargs['samples'] = samples

        return Location(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of Location')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'code': obj.code,
            'registered_voters': obj.registered_voters,
            'lat': obj.lat,
            'lon': obj.lon,
            'extra_data': obj.extra_data,
            'location_set': obj.location_set.uuid.hex,
            'location_type': obj.location_type.uuid.hex,
            'samples': [s.uuid.hex for s in obj.samples]
        }


class LocationSetSerializer(object):
    __model__ = LocationSet

    def deserialize_one(self, data):
        return LocationSet(**data)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of LocationSet')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'slug': obj.slug
        }


class LocationDataFieldSerializer(object):
    __model__ = LocationDataField

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs['location_set_id'] = location_set_id

        return LocationDataField(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of LocationDataField')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'label': obj.label,
            'visible_in_lists': obj.visible_in_lists,
            'location_set': obj.location_set.uuid.hex,
        }


class LocationTypeSerializer(object):
    __model__ = LocationType

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs['location_set_id'] = location_set_id

        return LocationType(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of LocationType')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'is_administrative': obj.is_administrative,
            'is_political': obj.is_political,
            'has_registered_voters': obj.has_registered_voters,
            'slug': obj.slug,
            'location_set': obj.location_set.uuid.hex,
        }


class LocationPathSerializer(object):
    __model__ = LocationPath

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()
        ancestor_id = Location.query.filter_by(
            uuid=data['ancestor_location']
        ).with_entities(Location.id).scalar()
        descendant_id = Location.query.filter_by(
            uuid=data['descendant_location']
        ).with_entities(Location.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs.pop('ancestor_location')
        kwargs.pop('descendant_location')
        kwargs['location_set_id'] = location_set_id
        kwargs['ancestor_id'] = ancestor_id
        kwargs['descendant_id'] = descendant_id

        return LocationPath(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of LocationPath')

        return {
            'location_set': obj.location_set.uuid.hex,
            'ancestor_location': obj.ancestor_location.uuid.hex,
            'descendant_location': obj.descendant_location.uuid.hex,
            'depth': obj.depth
        }


class LocationTypePathSerializer(object):
    __model__ = LocationTypePath

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()
        ancestor_id = LocationType.query.filter_by(
            uuid=data['ancestor_location_type']
        ).with_entities(LocationType.id).scalar()
        descendant_id = LocationType.query.filter_by(
            uuid=data['descendant_location_type']
        ).with_entities(LocationType.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs.pop('ancestor_location_type')
        kwargs.pop('descendant_location_type')
        kwargs['location_set_id'] = location_set_id
        kwargs['ancestor_id'] = ancestor_id
        kwargs['descendant_id'] = descendant_id

        return LocationTypePath(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of LocationTypePath')

        return {
            'location_set': obj.location_set.uuid.hex,
            'ancestor_location_type': obj.ancestor_location_type.uuid.hex,
            'descendant_location_type': obj.descendant_location_type.uuid.hex,
            'depth': obj.depth
        }


class SampleSerializer(object):
    __model__ = Sample

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs['location_set_id'] = location_set_id

        return Sample(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of Sample')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name
        }


class LocationSetArchiveSerializer(ArchiveSerializer):
    __model__ = LocationSet

    def deserialize(self, zip_file):
        pass

    def serialize(self, event, zip_file):
        location_set = event.location_set

        if location_set:
            self.serialize_location_set(location_set, zip_file)
            self.serialize_samples(location_set.samples, zip_file)
            self.serialize_location_types(
                location_set.location_types, zip_file)
            self.serialize_location_type_paths(
                location_set.location_type_paths, zip_file)
            self.serialize_locations(location_set.locations, zip_file)
            self.serialize_location_paths(
                location_set.location_paths, zip_file)
            self.serialize_extra_fields(location_set.extra_fields, zip_file)
            self.serialize_sample_nodes(location_set, zip_file)

    def serialize_location_set(self, obj, zip_file):
        serializer = LocationSetSerializer()
        data = serializer.serialize_one(obj)

        with zip_file.open('location_set.ndjson', 'w') as f:
            f.write(json.dumps(data).encode('utf-8'))

    def serialize_samples(self, samples, zip_file):
        serializer = SampleSerializer()

        with zip_file.open('samples.ndjson', 'w') as f:
            for sample in samples:
                data = serializer.serialize_one(sample)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_sample_nodes(self, location_set, zip_file):
        sample_entries = location_set.samples.join(
            Location.samples).with_entities(Sample.uuid, Location.uuid)

        with zip_file.open('sample_nodes.ndjson', 'w') as f:
            for sample_uuid, location_uuid in sample_entries:
                data = json.dumps((sample_uuid.hex, location_uuid.hex))
                line = f'{data}\n'
                f.write(line.encode('utf-8'))

    def serialize_location_types(self, location_types, zip_file):
        serializer = LocationTypeSerializer()

        with zip_file.open('location_types.ndjson', 'w') as f:
            for location_type in location_types:
                data = serializer.serialize_one(location_type)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_location_paths(self, location_paths, zip_file):
        serializer = LocationPathSerializer()

        with zip_file.open('location_paths.ndjson', 'w') as f:
            for location_path in location_paths:
                data = serializer.serialize_one(location_path)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_location_type_paths(self, location_type_paths, zip_file):
        serializer = LocationTypePathSerializer()

        with zip_file.open('location_type_paths.ndjson', 'w') as f:
            for location_type_path in location_type_paths:
                data = serializer.serialize_one(location_type_path)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_locations(self, locations, zip_file):
        serializer = LocationSerializer()

        with zip_file.open('locations.ndjson', 'w') as f:
            for location in locations:
                data = serializer.serialize_one(location)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_extra_fields(self, extra_fields, zip_file):
        serializer = LocationDataFieldSerializer()

        with zip_file.open('location_data_fields.ndjson', 'w') as f:
            for extra_field in extra_fields:
                data = serializer.serialize_one(extra_field)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))
