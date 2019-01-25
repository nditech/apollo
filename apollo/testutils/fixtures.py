# -*- coding: utf-8 -*-
import logging
import pathlib
import warnings

from sqlalchemy.sql import text

from apollo.core import db

logger = logging.getLogger(__name__)


def load_sql_fixture(fixture):
    source_file = pathlib.Path(fixture)
    if source_file.exists() and source_file.is_file():
        query_text = text(source_file.read_text())
        try:
            # create connection and start transation
            with db.engine.begin() as conn:
                conn.execute(query_text)
        except Exception as ex:
            logger.exception('Error occurred executing fixture statement(s)')
    else:
        warnings.warn(f'Invalid fixture specified: {source_file}')
