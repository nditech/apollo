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
            params.update(deployment=g.get(u'deployment'),
                          events=g.get(u'event'))
        except RuntimeError:
            pass

        # if there's an 'event' kwarg, make it overwrite the 'events'
        # one
        event = kwargs.pop(u'event', None)
        params.update(kwargs)
        if event:
            params.update(events=event)

        return params
