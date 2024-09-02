from contextlib import suppress

from sqlalchemy.orm import Query
from sqlalchemy.sql import visitors

from apollo.dal.models import BaseModel


def has_model(query: Query, model: BaseModel) -> bool:
    '''
    This function goes over the select statement for a query
    and checks to see if the model class `model` is joined
    in the query.
    '''
    # thanks to the very helpful poster who posted on SO:
    # https://stackoverflow.com/a/66855484
    for visitor in visitors.iterate(query.statement):
        if visitor.__visit_name__ == "binary":
            for vis in visitors.iterate(visitor):
                with suppress(AttributeError):
                    if model.__table__.fullname == vis.table.fullname:
                        return True

        if visitor.__visit_name__ == "table":
            with suppress(TypeError):
                if model == visitor.entity_namespace:
                    return True

        if visitor.__visit_name__ == "column":
            with suppress(AttributeError):
                if model.__table__.fullname == visitor.table.fullname:
                    return True

    return False
