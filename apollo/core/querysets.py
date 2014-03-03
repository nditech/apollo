from mongoengine import QuerySet


class LocationQuerySet(QuerySet):
    '''Custom queryset class for filtering locations under a specified
    location.'''
    def is_within(self, location):
        '''
        Filters out locations that are not descendants of :param: `location`
        '''
        return self.filter(ancestors_ref__in=[location])
