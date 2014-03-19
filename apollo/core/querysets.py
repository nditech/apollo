from flask.ext.mongoengine import BaseQuerySet
from mongoengine import Q
from pandas import DataFrame


class LocationQuerySet(BaseQuerySet):
    '''Custom queryset class for filtering locations under a specified
    location.'''
    def filter_in(self, location):
        '''
        Filters out locations that are not descendants of :param: `location`
        '''
        return self(Q(id=location.id) | Q(ancestors_ref=location))


class SubmissionQuerySet(BaseQuerySet):
    # most of the fields below are DBRef fields or not useful to
    # our particular use case.
    DEFAULT_EXCLUDED_FIELDS = [
        'id', 'form', 'created', 'updated', 'location', 'contributor'
    ]

    def filter_in(self, location):
        query_kwargs = {
            'location_name_path__{}'.format(location.location_type): location.name
        }
        return self(Q(location=location) | Q(**query_kwargs))

    def to_dataframe(self, selected_fields=None, excluded_fields=None):
        if excluded_fields:
            qs = self.exclude(*excluded_fields)
        else:
            qs = self.exclude(*SubmissionQuerySet.DEFAULT_EXCLUDED_FIELDS)
        if selected_fields:
            qs = self.only(*selected_fields)

        return DataFrame(list(qs.as_pymongo()))
