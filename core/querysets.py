from django_orm.postgresql.hstore.queryset import HStoreQuerySet


class SubmissionQuerySet(HStoreQuerySet):
    def is_complete(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = '"core_submission"."data" ?& ARRAY[%s]' % (','.join(['%s'] * len(fields)))
        return self.extra(where=[_where], params=fields) if fields else self

    def is_missing(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = 'NOT "core_submission"."data" ?| ARRAY[%s]' % (','.join(['%s'] * len(fields)))
        return self.extra(where=[_where], params=fields) if fields else self.none()

    def is_partial(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        _where = '"core_submission"."data" ?| ARRAY[%(fields)s] AND NOT "core_submission"."data" ?& ARRAY[%(fields)s]' % \
            {'fields': ','.join(['%s'] * len(fields))}
        return self.extra(where=[_where], params=fields * 2) if fields else self

    def is_within(self, location):
        return self.filter(location__pk__in=[loc.pk for loc in location.get_descendants(include_self=True)])
