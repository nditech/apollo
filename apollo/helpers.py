# -*- coding: utf-8 -*-
import importlib

from flask import Blueprint
import magic
import pandas as pd
import pkgutil

CSV_MIMETYPES = [
    "text/csv",
    "text/plain",
    "application/csv",
    "text/plain",
    "text/x-csv",
    "application/x-csv",
    "text/comma-separated-values",
    "text/x-comma-separated-values",
]

EXCEL_MIMETYPES = [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


def register_blueprints(app, package_name, package_path):
    """Register all Blueprint instances on the specified Flask application
    found in all modules for the specified package.

    :param app: the Flask application
    :param package_name: the package name
    :param package_path: the package path
    """
    rv = []
    for _, name, _ in pkgutil.iter_modules(package_path):
        if name.startswith('views_'):
            m = importlib.import_module('%s.%s' % (package_name, name))
            for item in dir(m):
                item = getattr(m, item)
                if isinstance(item, Blueprint):
                    app.register_blueprint(item)
                rv.append(item)
    return rv


def _make_choices(qs, placeholder=None):
    """Helper method for generating choices for :class:`SelectField`
    instances.
    """
    if placeholder:
        return [['', placeholder]] + [[str(i[0]), i[1]] for i in list(qs)]
    else:
        return [['', '']] + [[str(i[0]), i[1]] for i in list(qs)]


def load_source_file(source_file):
    # peek into file and read first 1kB, then reset pointer
    mimetype = magic.from_buffer(source_file.read(), mime=True)
    source_file.seek(0)

    if mimetype in CSV_MIMETYPES:
        # likely a CSV file
        df = pd.read_csv(source_file, dtype=str).fillna('')
    elif mimetype in EXCEL_MIMETYPES:
        # likely an Excel spreadsheet, read all data as strings
        xl = pd.ExcelFile(source_file)
        ncols = xl.book.sheet_by_index(0).ncols
        df = xl.parse(0, converters={i: str for i in range(ncols)}).fillna('')
    else:
        raise RuntimeError('Unknown file type')

    return df
