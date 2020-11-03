# -*- coding: utf-8 -*-
from authlib.flask.client import OAuth
from collections import OrderedDict
from flask import redirect, url_for
from flask_admin import expose, Admin, AdminIndexView
from flask_apispec import FlaskApiSpec
from flask_babelex import Babel
from flask_caching import Cache
from flask_cors import CORS
try:
    from flask_debugtoolbar import DebugToolbarExtension
    fdt_available = True
except ImportError:
    fdt_available = False
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_menu import Menu
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import DEFAULTS, UploadSet
from flask_gravatar import Gravatar
from flask_webpack import Webpack
from flask_wtf.csrf import CSRFProtect
from raven.contrib.flask import Sentry
import six
from sqlalchemy import and_, or_
from wtforms import Form, fields

from apollo.sentry_ext import ApolloRavenClient


class AdminHome(AdminIndexView):
    @expose('/')
    def index(self):
        return redirect(url_for('dashboard.index'))


admin = Admin(
    name='Apollo', index_view=AdminHome(name='Dashboard'))
babel = Babel()
cache = Cache()
cors = CORS()
db = SQLAlchemy(session_options={'expire_on_commit': False})
jwt_manager = JWTManager()
mail = Mail()
menu = Menu()
migrate = Migrate()
oauth = OAuth()
red = FlaskRedis()
security = Security()
gravatar = Gravatar(size=25, default="identicon", use_ssl=True)
sentry = Sentry(client_cls=ApolloRavenClient)
csrf = CSRFProtect()
debug_toolbar = DebugToolbarExtension() if fdt_available else None
uploads = UploadSet('uploads', DEFAULTS)
webpack = Webpack()
docs = FlaskApiSpec()


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

    def filter(self, queryset, value, **kwargs):
        return (None, None)

    def queryset_(self, queryset, value, **kwargs):
        return queryset

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


class BooleanFilter(Filter):
    field_class = fields.BooleanField


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
                filters = list(base.declared_filters.items()) + filters

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
            constraints_and = []
            constraints_or = []
            # force form validation - otherwise, errors won't be picked up
            self.form.validate()

            for name, filter_ in six.iteritems(self.declared_filters):
                field = self.form[name]
                if field.errors:
                    continue

                qs = filter_.queryset_(qs, field.data)

                and_constraint, or_constraint = filter_.filter(
                    qs, field.data, form=self.form)

                if and_constraint is not None:
                    constraints_and.append(and_constraint)
                if or_constraint is not None:
                    constraints_or.append(or_constraint)

            self._qs = qs.filter(
                and_(*constraints_and)).filter(or_(*constraints_or))

        return self._qs


class FilterSet(six.with_metaclass(FilterSetMetaclass, BaseFilterSet)):
    pass
