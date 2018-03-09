# -*- coding: utf-8 -*-
import importlib

from flask import Blueprint
import magic
import pandas as pd
import pkgutil


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

    if mimetype.startswith('text'):
        # likely a CSV file
        df = pd.read_csv(source_file, dtype=str).fillna('')
    elif mimetype.startswith('application'):
        # likely an Excel spreadsheet
        df = pd.read_excel(source_file, 0).fillna('')
    else:
        raise RuntimeError('Unknown file type')

    return df
