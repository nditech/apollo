from django_orm.postgresql.hstore import HStoreManager
from .querysets import SubmissionQuerySet, SearchableLocationQuerySet


class SubmissionManager(HStoreManager):
    def get_query_set(self):
        return SubmissionQuerySet(self.model)


class ObserverManager(HStoreManager):
    def get_query_set(self):
        return SearchableLocationQuerySet(self.model)
