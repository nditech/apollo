import bson
import pymongo


def load_fixtures(database, fixture_path):
    '''loads JSON fixtures.
    :param: `database` a PyMongo database object
    '''
    with open(fixture_path) as f:
        data = bson.json_util.loads(f.read())

    for key in data.keys():
        try:
            database[key].insert(data[key])
        except pymongo.errors.DuplicateKeyError:
            continue
