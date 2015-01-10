from collections import OrderedDict
from flask import g, abort
from flask.ext.admin import Admin
from flask.ext.babel import Babel
from flask.ext.cache import Cache
from flask.ext.mail import Mail
from flask.ext.menu import Menu
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security
from flask.ext.gravatar import Gravatar
from flask.ext.wtf.csrf import CsrfProtect
from mongoengine.base import ValidationError
from raven.contrib.flask import Sentry
import six
from wtforms import Form, fields


admin = Admin(name='Apollo')
babel = Babel()
cache = Cache()
db = MongoEngine()
mail = Mail()
menu = Menu()
security = Security()
gravatar = Gravatar(size=25, default="identicon", use_ssl=True)
sentry = Sentry()
csrf = CsrfProtect()


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

        try:
            return self.__model__.objects.filter(**kwargs)
        except ValidationError:
            abort(404)

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
        except (self.__model__.DoesNotExist, ValidationError):
            return None

    # def get_all(self, **kwargs):
    #     """Returns a list of instances of the service's model with the
    #     specified keyword arguments as filter parameters.

    #     :param **kwargs: filter parameters
    #     """
    #     kwargs = self._set_default_filter_parameters(kwargs)

    #     return self.find(**kwargs)

    def get_or_404(self, **kwargs):
        """Returns an instance of the service's model with the specified
        parameters or raises a 404 error if an instance with the specified
        parameters does not exist.

        :param **kwargs: filter parameters
        """
        kwargs = self._set_default_filter_parameters(kwargs)

        return self.__model__.objects.get_or_404(**kwargs)

    def get_or_create(self, **kwargs):
        """Retrieves an instance based on search parameters specified by the
        keyword arguments or if it is not found, create one.

        :param **kwargs: filter parameters
        """
        return self.get(**kwargs) or self.create(**kwargs)

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


class Filter(object):
    """Enables filtering a queryset on one parameter. Several filters
    can (and should) be combined into a `class`FilterSet, which can be
    used to generate a form for receiving the necessary parameters for
    filtering.

    This base class doesn't do much, and will raise an exception if it's
    used directly. Subclasses should override `method`filter() to perform
    their own filtering.

    This is a subset of what django-filter offers.
    """
    creation_counter = 0
    field_class = fields.Field

    def __init__(self, name=None, widget=None, **kwargs):
        self.extra = kwargs
        self.name = name
        self.widget = widget

        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1

    def filter(self, queryset, value):
        raise NotImplementedError()

    @property
    def field(self):
        """A HTML form field for receiving input for this `class`Filter.
        """
        if not hasattr(self, '_field'):
            self._field = self.field_class(widget=self.widget, **self.extra)
        return self._field


class CharFilter(Filter):
    field_class = fields.StringField


class ChoiceFilter(Filter):
    field_class = fields.SelectField


def get_declared_filters(bases, attrs, use_base_filters=True):
    """Creates an ordered dictionary of all `class`Filter instances
    declared in a `class`FilterSet, and optionally assigns a name to
    each one that doesn't have one explicitly set. Used by
    `class`FilterSetMetaclass to create the `class`FilterSet class
    object."""
    filters = []
    for filter_name, obj in list(attrs.items()):
        if isinstance(obj, Filter):
            if getattr(obj, 'name', None) is None:
                obj.name = filter_name
            filters.append((filter_name, obj))
    filters.sort(key=lambda x: x[1].creation_counter)

    if use_base_filters:
        for base in bases[::-1]:
            if hasattr(base, 'declared_filters'):
                filters = base.declared_filters.items() + filters

    return OrderedDict(filters)


class FilterSetMetaclass(type):
    """Metaclass for `class`FilterSet"""

    def __new__(cls, name, bases, attrs):
        declared_filters = get_declared_filters(bases, attrs)
        new_class = super(FilterSetMetaclass, cls).__new__(
            cls, name, bases, attrs)
        new_class.declared_filters = declared_filters

        return new_class


class BaseFilterSet(object):
    """This class serves as a container for `class`Filter instances.
    Users should subclass `class`FilterSet and add `class`Filter
    instances as class attributes. This class has a cached form property
    that can be used to render a HTML form for filtering a relevant
    queryset. When processing user data using the form, invalid
    inputs do not affect the filtering process."""
    def __init__(self, queryset, data=None, prefix=''):
        self.queryset = queryset
        self.data = data
        self.is_bound = data is not None
        self.prefix = prefix

    @property
    def form(self):
        """Generates a HTML form that can be used to receive user input
        for filtering the queryset.
        """
        if not hasattr(self, '_form'):
            fields = OrderedDict(
                ((name, filter_.field) for name, filter_ in six.iteritems(
                    self.declared_filters)))
            form_class = type(
                str('{}Form'.format(self.__class__.__name__)),
                (Form,),
                fields
            )
            if self.is_bound:
                self._form = form_class(self.data, prefix=self.prefix)
            else:
                self._form = form_class(prefix=self.prefix)
        return self._form

    @property
    def qs(self):
        """A cached queryset that is generated by filtering the initial
        queryset based on the valid form values set.
        """
        if not hasattr(self, '_qs'):
            qs = self.queryset
            # force form validation - otherwise, errors won't be picked up
            self.form.validate()

            for name, filter_ in six.iteritems(self.declared_filters):
                field = self.form[name]
                if field.errors:
                    continue
                qs = filter_.filter(qs, field.data)

            self._qs = qs

        return self._qs


class FilterSet(six.with_metaclass(FilterSetMetaclass, BaseFilterSet)):
    pass
