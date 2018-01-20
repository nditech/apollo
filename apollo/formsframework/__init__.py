# -*- coding: utf-8 -*-
from apollo.core import Service
from apollo.formsframework.models import Form
from flask import g


class FormsService(Service):
    __model__ = Form

    def _set_default_filter_parameters(self, kwargs):
        """Updates the kwargs by setting the default filter parameters
        if available.

        :param kwargs: a dictionary of parameters
        """
        params = {}
        try:
            deployment = g.get('deployment')
            if deployment:
                params['deployment'] = deployment
            event = g.get('event')
            if event:
                params['events'] = event
        except RuntimeError:
            pass

        # if there's an 'event' kwarg, make it overwrite the 'events'
        # one
        event = kwargs.pop('event', None)
        params.update(kwargs)
        if event:
            params.update(events=event)

        return params
