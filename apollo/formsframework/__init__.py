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
        try:
            deployment = kwargs.get('deployment', g.get('deployment'))
            event = kwargs.get('event', g.get('event'))
            if deployment:
                kwargs.update({'deployment': deployment})
            if event:
                kwargs.update({'events': event})
        except RuntimeError:
            pass

        return kwargs
