from flask import abort, g
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface
from flask.ext.security import Security

babel = Babel()
db = MongoEngine()
mail = Mail()
security = Security()


class Service(object):
    """A :class:`Service` instance encapsulates common MongoEngine document
    operations in the context of a :class:`Flask` application.
    """
    __model__ = None

    def _isinstance(self, model, raise_error=True):
        """Checks if the specified model instance matches the service's model.
        By default this method will raise a `ValueError` if the model is not
        the expected type.

        :param model: the model instance to check
        :param raise_error: flag to raise an error on a mismatch
        """
        rv = isinstance(model, self.__model__)
        if not rv and raise_error:
            raise ValueError('%s is not of type %s' % (model, self.__model__))
        return rv

    def _preprocess_params(self, kwargs):
        """Returns a preprocessed dictionary of parameters. Used by default
        before creating a new instance or updating an existing instance.

        :param kwargs: a dictionary of parameters
        """
        kwargs.pop('csrf_token', None)
        return kwargs

    def _set_default_filter_parameters(self, kwargs):
        """Updates the kwargs by setting the default filter parameters
        if available.

        :param kwargs: a dictionary of parameters
        """
        try:
            deployment = kwargs.get('deployment', g.get('deployment'))
            if deployment:
                kwargs.update({'deployment': deployment})
        except RuntimeError:
            pass

        return kwargs

    def save(self, model):
        """Saves the model to the database and returns the model

        :param model: the model to save
        """
        model.save()
        return model

    def all(self):
        """Returns a generator containing all instances of the service's model.
        """
        return self.__model__.objects.all()

    def find(self, **kwargs):
        """Returns a list of instances of the service's model filtered by the
        specified key word arguments.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        return self.__model__.objects.filter(**kwargs)

    def get(self, **kwargs):
        """Returns an instance of the service's model with the specified
        filter parameters.
        Returns `None` if an instance with the specified filter parameters
        does not exist.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        try:
            return self.__model__.objects.get(**kwargs)
        except self.__model__.DoesNotExist:
            return None

    def get_all(self, **kwargs):
        """Returns a list of instances of the service's model with the
        specified keyword arguments as filter parameters.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        return self.find(**kwargs)

    def get_or_404(self, **kwargs):
        """Returns an instance of the service's model with the specified
        parameters or raises a 404 error if an instance with the specified
        parameters does not exist.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        try:
            self.get(**kwargs)
        except __model__.DoesNotExist:
            abort(404)

    def first(self, **kwargs):
        """Returns the first instance found of the service's model filtered by
        the specified key word arguments.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        return self.find(**kwargs).first()

    def new(self, **kwargs):
        """Returns a new, unsaved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        return self.__model__(**self._preprocess_params(kwargs))

    def create(self, **kwargs):
        """Returns a new, saved instance of the service's model class.

        :param **kwargs: instance parameters
        """
        return self.save(self.new(**kwargs))

    def update(self, model, **kwargs):
        """Returns an updated instance of the service's model class.

        :param model: the model to update
        :param **kwargs: update parameters
        """
        self._isinstance(model)
        for k, v in self._preprocess_params(kwargs).items():
            setattr(model, k, v)
        self.save(model)
        return model

    def delete(self, model):
        """Immediately deletes the specified model instance.

        :param model: the model instance to delete
        """
        self._isinstance(model)
        return model.delete()
