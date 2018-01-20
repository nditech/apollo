# -*- coding: utf-8 -*-
from apollo import services


def nuke_locations():
    # nuke submissions
    services.submissions.find().delete()

    # nuke participants
    services.participants.find().delete()

    # nuke samples
    services.samples.find().delete()

    # nuke locations
    services.locations.find().delete()
