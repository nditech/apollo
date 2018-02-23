# -*- coding: utf-8 -*-
from apollo import services
from apollo.core import db


def nuke_locations(location_set_id):
    # nuke locations
    services.locations.find(location_set_id=location_set_id).delete()
    db.session.commit()
