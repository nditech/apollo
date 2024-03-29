# -*- coding: utf-8 -*-
import json

from sqlalchemy import String, cast, func

from apollo.dal.serializers import ArchiveSerializer
from apollo.locations.models import Location, LocationSet
from apollo.participants.models import (
    Participant, ParticipantDataField, ParticipantPartner, ParticipantRole,
    ParticipantSet, PhoneContact)


class ParticipantSerializer(object):
    __model__ = Participant

    def deserialize_one(self, data):
        participant_set_id = ParticipantSet.query.filter_by(
            uuid=data['participant_set']
        ).with_entities(ParticipantSet.id).scalar()
        partner_id = ParticipantPartner.query.filter_by(
            uuid=data['partner']
        ).with_entities(ParticipantPartner.id).scalar()
        role_id = ParticipantRole.query.filter_by(
            uuid=data['role']
        ).with_entities(ParticipantRole.id).scalar()

        if data['location']:
            location_id = Location.query.filter_by(
                uuid=data['location']
            ).with_entities(Location.id).scalar()
        else:
            location_id = None

        kwargs = data.copy()
        kwargs.pop('participant_set')
        kwargs.pop('partner')
        kwargs.pop('role')
        kwargs.pop('location')
        kwargs['participant_set_id'] = participant_set_id
        kwargs['location_id'] = location_id
        kwargs['role_id'] = role_id
        kwargs['partner_id'] = partner_id

        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of ParticipantSet')

        return {
            'uuid': obj.uuid.hex,
            'full_name': {
                locale: name
                for locale, name in obj.full_name_translations.items()
            },
            'first_name': {
                locale: name
                for locale, name in obj.first_name_translations.items()
            },
            'other_names': {
                locale: name
                for locale, name in obj.other_names_translations.items()
            },
            'last_name': {
                locale: name
                for locale, name in obj.last_name_translations.items()
            },
            'participant_id': obj.participant_id,
            'email': obj.email,
            'role': obj.role.uuid.hex if obj.role else None,
            'location': obj.location.uuid.hex if obj.location else None,
            'partner': obj.partner.uuid.hex if obj.partner else None,
            'gender': obj.gender.code if obj.gender else '',
            'locale': obj.locale if obj.locale else '',
            'message_count': obj.message_count,
            'accurate_message_count': obj.accurate_message_count,
            'completion_rating': obj.completion_rating,
            'device_id': obj.device_id,
            'password': obj.password,
            'extra_data': obj.extra_data
        }


class ParticipantSetSerializer(object):
    __model__ = ParticipantSet

    def deserialize_one(self, data):
        location_set_id = LocationSet.query.filter_by(
            uuid=data['location_set']).with_entities(LocationSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('location_set')
        kwargs['location_set_id'] = location_set_id
        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of ParticipantSet')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'slug': obj.slug,
            'location_set': obj.location_set.uuid.hex
        }


class ParticipantDataFieldSerializer(object):
    __model__ = ParticipantDataField

    def deserialize_one(self, data):
        participant_set_id = ParticipantSet.query.filter_by(
            uuid=data['participant_set']
        ).with_entities(ParticipantSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('participant_set')
        kwargs['participant_set_id'] = participant_set_id

        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of ParticipantDataField')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'label': obj.label,
            'visible_in_lists': obj.visible_in_lists,
            'participant_set': obj.participant_set.uuid.hex
        }


class ParticipantPartnerSerializer(object):
    __model__ = ParticipantPartner

    def deserialize_one(self, data):
        participant_set_id = ParticipantSet.query.filter_by(
            uuid=data['participant_set']
        ).with_entities(ParticipantSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('participant_set')
        kwargs['participant_set_id'] = participant_set_id

        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of ParticipantPartner')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'participant_set': obj.participant_set.uuid.hex
        }


class ParticipantRoleSerializer(object):
    __model__ = ParticipantRole

    def deserialize_one(self, data):
        participant_set_id = ParticipantSet.query.filter_by(
            uuid=data['participant_set']
        ).with_entities(ParticipantSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('participant_set')
        kwargs['participant_set_id'] = participant_set_id

        return self.__model__(**data)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not instance of ParticipantRole')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'participant_set': obj.participant_set.uuid.hex
        }


class ParticipantSetArchiveSerializer(ArchiveSerializer):
    def deserialize(self, zip_file):
        pass

    def serialize(self, event, zip_file):
        participant_set = event.participant_set

        if participant_set:
            self.serialize_participant_set(participant_set, zip_file)
            self.serialize_extra_fields(participant_set.extra_fields, zip_file)
            self.serialize_partners(participant_set.participant_partners,
                                    zip_file)
            self.serialize_roles(participant_set.participant_roles, zip_file)
            self.serialize_participants(participant_set.participants, zip_file)
            self.serialize_participant_phones(participant_set, zip_file)

    def serialize_participant_set(self, obj, zip_file):
        serializer = ParticipantSetSerializer()
        data = serializer.serialize_one(obj)

        with zip_file.open('participant_set.ndjson', 'w') as f:
            f.write(json.dumps(data).encode('utf-8'))

    def serialize_extra_fields(self, extra_fields, zip_file):
        serializer = ParticipantDataFieldSerializer()

        with zip_file.open('participant_data_fields.ndjson', 'w') as f:
            for extra_field in extra_fields:
                data = serializer.serialize_one(extra_field)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_partners(self, partners, zip_file):
        serializer = ParticipantPartnerSerializer()

        with zip_file.open('participant_partners.ndjson', 'w') as f:
            for partner in partners:
                data = serializer.serialize_one(partner)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_roles(self, roles, zip_file):
        serializer = ParticipantRoleSerializer()

        with zip_file.open('participant_roles.ndjson', 'w') as f:
            for role in roles:
                data = serializer.serialize_one(role)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_participants(self, participants, zip_file):
        serializer = ParticipantSerializer()

        with zip_file.open('participants.ndjson', 'w') as f:
            for participant in participants:
                data = serializer.serialize_one(participant)
                line = f'{json.dumps(data)}\n'
                f.write(line.encode('utf-8'))

    def serialize_participant_phones(self, participant_set, zip_file):
        query = participant_set.participants.join(
            PhoneContact).with_entities(
                cast(Participant.uuid, String), PhoneContact.number,
                func.extract('epoch', PhoneContact.created),
                func.extract('epoch', PhoneContact.updated),
                PhoneContact.verified)

        with zip_file.open('phone-contacts.ndjson', 'w') as f:
            for record in query:
                line = f'{json.dumps(record)}\n'
                f.write(line.encode('utf-8'))
