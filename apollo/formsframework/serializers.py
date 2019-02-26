# -*- coding: utf-8 -*-
from apollo.formsframework.models import Form, FormSet


class FormSerializer(object):
    __model__ = Form

    def deserialize_one(self, data):
        form_set_id = FormSet.query.filter_by(
            uuid=data['form_set']).with_entities(FormSet.id).scalar()

        kwargs = data.copy()
        kwargs.pop('form_set')
        kwargs['form_set_id'] = form_set_id

        return self.__model__(**kwargs)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not of type Form')

        return {
            'uuid': obj.uuid.hex,
            'name': obj.name,
            'prefix': obj.prefix,
            'form_type': obj.form_type.code,
            'require_exclamation': obj.require_exclamation,
            'data': obj.data,
            'version_identifier': obj.version_identifier,
            'quality_checks': obj.quality_checks,
            'party_mappings': obj.party_mappings,
            'calculate_moe': obj.calculate_moe,
            'accredited_voters_tag': obj.accredited_voters_tag,
            'quality_checks_enabled': obj.quality_checks_enabled,
            'invalid_votes_tag': obj.invalid_votes_tag,
            'registered_voters_tag': obj.registered_voters_tag,
            'blank_votes_tag': obj.blank_votes_tag,
        }


class FormSetSerializer(object):
    __model__ = FormSet

    def deserialize_one(self, data):
        return self.__model__(**data)

    def serialize_one(self, obj):
        if not isinstance(obj, self.__model__):
            raise TypeError('Object is not of type FormSet')

        return {
            'name': obj.name,
            'slug': obj.slug,
            'uuid': obj.uuid.hex,
        }
