# -*- coding: utf-8 -*-
from flask import g
from raven.base import Client

from apollo import settings


class ApolloRavenClient(Client):
    def capture(self, event_type, data=None, date=None, time_spent=None,
            extra=None, stack=None, tags=None, **kwargs):

        extra = extra or {}
        extra.update({
            u'event': str(getattr(g, u'event', None)),
            u'apollo_version': getattr(settings, u'APOLLO_VERSION',
                u'Unspecified'),
        })

        return super(ApolloRavenClient, self).capture(event_type, data,
            date, time_spent, extra, stack, tags, **kwargs)
