import importlib
import magic
import pandas as pd
import pkgutil
import re

from flask import Blueprint
from apollo.locations.models import Location


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
        return [['', placeholder]] + [[unicode(i[0]), i[1]] for i in list(qs)]
    else:
        return [['', '']] + [[unicode(i[0]), i[1]] for i in list(qs)]


def stash_file(fileobj, user, event=None):
    from apollo.services import user_uploads
    upload = user_uploads.create(user=user, event=event)
    upload.data.put(fileobj)
    upload.save()
    upload.reload()

    return upload


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


def is_objectid(str):
    return bool(re.match('^[0-9a-fA-F]{24}$', str))


def compute_location_path(location):
    '''Given a :class:`apollo.locations.models.Location` instance,
    generates a dictionary with location type names as keys and
    location names as values. Due to lack of joins in MongoDB,
    this dictionary is useful for queries that retrieve submission
    and participant information within a location hierarchy.'''

    # we don't really expect the latter case, but for the former,
    # it's possible to have a participant with no location set
    if not location or not isinstance(location, Location):
        return None

    path = {
        ancestor.location_type: ancestor.name
        for ancestor in location.ancestors_ref
    }
    path.update({
        location.location_type: location.name
    })
    return path
