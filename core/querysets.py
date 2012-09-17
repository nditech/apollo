from django_orm.postgresql.hstore.queryset import HStoreQuerySet


class SubmissionQuerySet(HStoreQuerySet):
    def is_complete(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = 'data ?& ARRAY[%s]' % (','.join(['%s'] * len(fields)))
        return self.extra(where=[_where], params=fields)

    def is_missing(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = 'NOT data ?| ARRAY[%s]' % (','.join(['%s'] * len(fields)))
        return self.extra(where=[_where], params=fields)

    def is_partial(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = 'data ?| ARRAY[%(fields)s] AND NOT data ?& ARRAY[%(fields)s]' % \
            {'fields': ','.join(['%s'] * len(fields))}
        return self.extra(where=[_where], params=fields * 2)