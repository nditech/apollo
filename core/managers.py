from django_orm.postgresql.hstore import HStoreManager
from .querysets import SubmissionQuerySet


class SubmissionManager(HStoreManager):
    def get_query_set(self):
        return SubmissionQuerySet(self.model)