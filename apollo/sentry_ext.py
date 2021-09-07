# -*- coding: utf-8 -*-
from flask import current_app
from flask_login import current_user
from raven.base import Client

from apollo import settings


class ApolloRavenClient(Client):
    def capture(self, event_type, data=None, date=None, time_spent=None,
                extra=None, stack=None, tags=None, **kwargs):

        extra = extra or {}
        if current_app:
            with current_app.app_context():
                if current_user and not current_user.is_anonymous:
                    deployment = current_user.deployment
                    event = getattr(current_user, 'event', None)
                else:
                    deployment = None
                    event = None

                extra.update({
                    'deployment': getattr(deployment, 'name', 'Not Available'),
                    'event': getattr(event, 'name', 'Not Available'),
                    'version': getattr(settings, 'VERSION'),
                    'commit': getattr(settings, 'COMMIT'),
                })

        return super(ApolloRavenClient, self).capture(
            event_type, data, date, time_spent, extra, stack, tags, **kwargs)
