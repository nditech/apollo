from djorm_expressions.base import SqlExpression, RawExpression, OR, AND
from djorm_hstore.models import HStoreQueryset
from djorm_hstore.functions import HstorePeek
import pandas as pd
from .functions import *


class SearchableLocationQuerySet(HStoreQueryset):
    def is_within(self, location):
        return self.filter(
            location__pk__in=[
                loc['id'] for loc in location.nx_descendants(include_self=True)
            ])


class SubmissionQuerySet(SearchableLocationQuerySet):
    def is_complete(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        expr = OR(
            SqlExpression("data", "?&", fields),
            SqlExpression("master__data", "?&", fields))
        return self.where(expr) if fields else self

    def is_missing(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        expr = AND(
            ~SqlExpression("data", "?|", fields),
            ~SqlExpression("master__data", "?|", fields))
        return self.where(expr) if fields else self.none()

    def is_partial(self, group):
        fields = list(group.fields.values_list('tag', flat=True))
        # checks that either data is partial or master__data is partial
        # but none of either data or master__data is complete
        expr = OR(
            AND(
                OR(
                    AND(SqlExpression("data", "?|", fields),
                        ~SqlExpression("data", "?&", fields)),
                    AND(SqlExpression("master__data", "?|", fields),
                        ~SqlExpression("master__data", "?&", fields))
                ),
                AND(~SqlExpression("data", "?&", fields),
                    ~SqlExpression("master__data", "?&", fields))
            ),
            AND(
                AND(SqlExpression("data", "?|", fields),
                        ~SqlExpression("data", "?&", fields)),
                RawExpression('"core_submission"."master_id" IS NULL')
            )
        )
        return self.where(expr) if fields else self

    def data(self, tags):
        # this method enables access to the keys in the hstore field
        # directly from the model
        # e.g. .data(['AA']) will make it possible to access AA
        # viz a viz: instance.AA
        params = {field: HstorePeek("data", field) for field in tags}
        return self.annotate_functions(**params)

    def dataframe(self):
        records = []
        for submission in self.select_related('location'):
            _submission = {}
            location_tree = submission.location.nx_ancestors(include_self=True)
            for k in filter(lambda key: not key.startswith('flag'), submission.data.keys()):
                try:
                    _submission[k] = int(submission.data[k])
                except ValueError:
                    pass
            # for urban/rural groupings, include the location urban data
            if 'urban' in submission.location.data:
                _submission['urban'] = int(float(submission.location.data['urban']))
            for location_item in location_tree:
                _submission[location_item['type']] = location_item['name']
            records.append(_submission)
        return pd.DataFrame(records)

    def intdata(self, tags):
        # returns the integer version of `data` defined above
        # NOTE: This does not work well for fields that store multiple
        # integers in a comma separated fashion. It will only return
        # the first integer in such cases
        params = {field: HstoreIntegerValue("data", field) for field in tags}
        return self.annotate_functions(**params)
