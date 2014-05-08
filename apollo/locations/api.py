# from flask import url_for
from flask.ext.restful import Resource, fields as r_fields, marshal
# from marshmallow import Serializer, fields as m_fields

from .. import services

LOCATION_TYPE_FIELD_MAPPER = {
    'id': r_fields.String,
    'name': r_fields.String,
}


# class LocationTypeSerializer(Serializer):
#     # id needs to be specified here
#     # because ObjectIDs aren't JSON serializable
#     id = m_fields.String()
#     uri = m_fields.Method('get_item_endpoint')

#     class Meta:
#         fields = ('id', 'name', 'uri')

#     def get_item_endpoint(self, locationtype):
#         return url_for(
#             'locations.api.locationtype',
#             loc_type_id=unicode(locationtype.pk))


class LocationTypeItemResource(Resource):
    def get(self, loc_type_id):
        # marshal() converts a custom object/dictionary/list using the mapper
        # into a Python dict
        data = marshal(
            services.location_types.get_or_404(pk=loc_type_id),
            LOCATION_TYPE_FIELD_MAPPER)

        # for the Url field, the constructor argument must be a full
        # path, because it will be converted using Flask's url_for(),
        # in the output() call, and if you don't give something it can
        # convert, it will fail with a BuildError
        # also, for a single item, you really don't need the url specced,
        # but whatever
        urlfield = r_fields.Url('locations.api.locationtype')
        data['uri'] = urlfield.output('uri', {'loc_type_id': data['id']})

        return data


class LocationTypeListResource(Resource):
    def get(self):
        # marshal() can also handle a list or tuple of objects, but it only
        # checks for a list or tuple, so we need to convert the queryset
        # to a list
        dataset = marshal(
            list(services.location_types.find()),
            LOCATION_TYPE_FIELD_MAPPER
        )

        for d in dataset:
            urlfield = r_fields.Url('locations.api.locationtype')
            d['uri'] = urlfield.output('uri', {'loc_type_id': d['id']})

        return dataset

        # same as the code above, except using marshmallow for
        # serialization. A Serializer can serialize an interable of objects
        # if you pass argument many=True to the constructor
        # return LocationTypeSerializer(
        #     services.location_types.find(),
        #     many=True
        # ).data
