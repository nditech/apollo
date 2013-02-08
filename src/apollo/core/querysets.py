from django_orm.core.sql import SqlExpression, OR, AND
from django_orm.postgresql.hstore.queryset import HStoreQuerySet


class SearchableLocationQuerySet(HStoreQuerySet):
    def is_within(self, location):
        return self.filter(location__pk__in=[loc['id'] for loc in location.nx_descendants(include_self=True)])


class SubmissionQuerySet(SearchableLocationQuerySet):
    def is_complete(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        return self.where(SqlExpression("data", "?&", fields)) if fields else self

    def is_missing(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        return self.where(~SqlExpression("data", "?|", fields)) if fields else self.none()

    def is_partial(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        return self.where(AND(SqlExpression("data", "?|", fields), ~SqlExpression("data", "?&", fields))) \
                if fields else self

    def data(self, tags):
        _select = dict([(tag, '"core_submission"."data"->%s' % ("'%s'" % (tag,))) for tag in tags])
        return self.extra(select=_select)
