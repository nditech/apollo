# -*- coding: utf-8 -*-
from flask import current_app, g
from raven.base import Client

from apollo import settings


class ApolloRavenClient(Client):
    def capture(self, event_type, data=None, date=None, time_spent=None,
            extra=None, stack=None, tags=None, **kwargs):

        extra = extra or {}

        with current_app.app_context():
            extra.update({
                'deployment': str(getattr(g, 'deployment', None)),
                'event': str(getattr(g, 'event', None)),
                'apollo_version': getattr(settings, 'APOLLO_VERSION',
                    'Unspecified'),
            })

        return super(ApolloRavenClient, self).capture(event_type, data,
            date, time_spent, extra, stack, tags, **kwargs)
