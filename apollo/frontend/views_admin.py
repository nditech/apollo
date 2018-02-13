# -*- coding: utf-8 -*-
import base64
from flask import flash, request
from flask_admin import form
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
# from flask_admin.contrib.sqla.form import CustomModelConverter
from flask_admin.form import rules
from flask_admin.model.form import converts
from flask_babelex import lazy_gettext as _
from flask_mongoengine.wtf import orm
from flask_security import current_user
from flask_security.utils import encrypt_password
from jinja2 import contextfunction
import magic
import pytz
from wtforms import FileField, PasswordField, SelectMultipleField
from apollo.core import admin, db
from apollo import models, models, settings
from apollo.frontend import forms


app_time_zone = pytz.timezone(settings.TIMEZONE)
utc_time_zone = pytz.utc

excluded_perm_actions = ['view_forms', 'access_event']

DATETIME_FORMAT_SPEC = '%Y-%m-%d %H:%M:%S %Z'

try:
    string_type = str
except NameError:
    string_type = str


# class DeploymentModelConverter(CustomModelConverter):
#     @converts('ParticipantPropertyName')
#     def conv_PropertyField(self, model, field, kwargs):
#         return orm.ModelConverter.conv_String(self, model, field, kwargs)


class BaseAdminView(ModelView):
    page_size = settings.PAGE_SIZE

    def is_accessible(self):
        '''For checking if the admin view is accessible.'''
        if current_user.is_anonymous:
            return False

        deployment = current_user.deployment
        role = models.Role.query.filter_by(
            deployment_id=deployment.id, name='admin').first()
        return current_user.has_role(role)


class DeploymentAdminView(BaseAdminView):
    can_create = False
    can_delete = False
    can_edit = True
    column_list = ('name', 'hostnames')
    form_edit_rules = [
        rules.FieldSet(
            (
                'name', 'allow_observer_submission_edit',
                'dashboard_full_locations', 'hostnames',
            ),
            _('Deployment')
        )
    ]

    form_columns = ['name', 'hostnames', 'dashboard_full_locations',
                    'allow_observer_submission_edit']

    def get_query(self):
        return models.Deployment.query.filter_by(
            id=current_user.deployment.id)


class EventAdminView(BaseAdminView):
    column_filters = ('name', 'start', 'end')
    column_list = ('name', 'start', 'end')
    form_columns = ('name', 'start', 'end')
    form_rules = [
        rules.FieldSet(('name', 'start', 'end'), _('Event'))
    ]


# class EventAdminView(ModelView):
#     # disallow event creation
#     # can_create = False

#     # what fields to be displayed in the list view
#     column_list = ('name', 'start', 'end')

#     # what fields filtering is allowed by
#     column_filters = ('name', 'start', 'end')

#     # rules for form editing. in this case, only the listed fields
#     # and the header for the field set
#     form_rules = [
#         rules.FieldSet(('name', 'start', 'end'), _('Event'))
#     ]

#     form_excluded_columns = ('deployment')

    def get_one(self, pk):
        event = super(EventAdminView, self).get_one(pk)

#         # setup permissions list
#         try:
#             entities = models.Need.objects.get(
#                 action='access_event', items=event).entities
#         except models.Need.DoesNotExist:
#             entities = []
#         event.roles = [str(i.pk) for i in entities]

        # convert start and end dates to app time zone
        event.start_date = utc_time_zone.localize(event.start_date).astimezone(
            app_time_zone)
        event.end_date = utc_time_zone.localize(event.end_date).astimezone(
            app_time_zone)
        return event

    @contextfunction
    def get_list_value(self, context, model, name):
        if name in ['start_date', 'end_date']:
            original = getattr(model, name, None)
            if original:
                return utc_time_zone.localize(original).astimezone(
                    app_time_zone).strftime(DATETIME_FORMAT_SPEC)

            return original

        return super(EventAdminView, self).get_list_value(context, model, name)

    def get_query(self):
        '''Returns the queryset of the objects to list.'''
        user = current_user._get_current_object()
        return models.Event.query.filter_by(deployment_id=user.deployment.id)

    def on_model_change(self, form, model, is_created):
        # if we're creating a new event, make sure to set the
        # deployment, since it won't appear in the form
        if is_created:
            model.deployment = current_user.deployment

        # also, convert the time zone to UTC
        model.start_date = app_time_zone.localize(model.start_date).astimezone(
            utc_time_zone)
        model.end_date = app_time_zone.localize(model.end_date).astimezone(
            utc_time_zone)

#     def after_model_change(self, form, model, is_created):
#         # remove event permission
#         models.Need.objects.filter(
#             action="access_event", items=model,
#             deployment=model.deployment).delete()

#         # create event permission
#         roles = models.Role.objects(pk__in=form.roles.data, name__ne='admin')
#         models.Need.objects.create(
#             action="access_event", items=[model], entities=roles,
#             deployment=model.deployment)

#     def scaffold_form(self):
#         form_class = super(EventAdminView, self).scaffold_form()
#         form_class.roles = SelectMultipleField(
#             _('Roles with access'),
#             choices=forms._make_choices(
#                 models.Role.objects(name__ne='admin').scalar('pk', 'name')),
#             widget=form.Select2Widget(multiple=True))

#         return form_class


class UserAdminView(BaseAdminView):
    '''Thanks to mrjoes and this Flask-Admin issue:
    https://github.com/mrjoes/flask-admin/issues/173
    '''
    column_list = ('email', 'roles', 'active')
    column_searchable_list = ('email',)
    form_columns = ('email', 'username', 'active')
    form_excluded_columns = ('password', 'confirmed_at', 'login_count',
                             'last_login_ip', 'last_login_at',
                             'current_login_at', 'deployment',
                             'current_login_ip', 'submission_comments')
    form_rules = [
        rules.FieldSet(('email', 'username', 'password2', 'active', 'roles'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.User.query.filter_by(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        if form.password2.data:
            model.password = encrypt_password(form.password2.data)
        if is_created:
            model.deployment = current_user.deployment

    def create_form(self, obj=None):
        form = super().create_form(obj)

        deployment = current_user.deployment
        role_choices = models.Role.query.with_entities(
            models.Role.id, models.Role.name).filter_by(
                deployment_id=deployment.id).all()

        form.roles.choices = role_choices

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        deployment = current_user.deployment
        role_choices = models.Role.query.with_entities(
            models.Role.id, models.Role.name).filter_by(
                deployment_id=deployment.id).all()

        form.roles.choices = role_choices
        form.roles.process(request.form, [role.id for role in obj.roles])

        return form

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password2 = PasswordField(_('New password'))
        form_class.roles = SelectMultipleField(
            _('Roles'), widget=form.Select2Widget(multiple=True))
        return form_class

    @action('disable', _('Disable'), _('Are you sure you want to disable selected users?'))
    def action_disable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = False
            role.save()
        flash(string_type(_('User(s) successfully disabled.')))

    @action('enable', _('Enable'), _('Are you sure you want to enable selected users?'))
    def action_enable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = True
            role.save()
        flash(string_type(_('User(s) successfully enabled.')))


class RoleAdminView(BaseAdminView):
    can_delete = False
    column_list = ('name', 'description')
    form_columns = ('name', 'description')

    def get_one(self, pk):
        deployment = current_user.deployment
        return models.Role.query.filter_by(
            deployment_id=deployment.id, id=pk).first_or_404()

#     def get_one(self, pk):
#         role = super(RoleAdminView, self).get_one(pk)
#         role.permissions = [
#             str(i) for i in models.Need.objects(
#                 entities=role, action__nin=excluded_perm_actions).scalar('pk')]
#         return role

#     def after_model_change(self, form, model, is_created):
#         # remove model from all permissions that weren't granted
#         # except for the excluded actions
#         for need in models.Need.objects(pk__nin=form.permissions.data,
#                                         action__nin=excluded_perm_actions):
#             need.update(pull__entities=model)

#         # add only the explicitly defined permissions
#         for pk in form.permissions.data:
#             models.Need.objects.get(pk=pk).update(add_to_set__entities=model)

#     def scaffold_form(self):
#         form_class = super(RoleAdminView, self).scaffold_form()
#         form_class.permissions = SelectMultipleField(
#             _('Permissions'),
#             choices=forms._make_choices(
#                 models.Need.objects(
#                     action__nin=excluded_perm_actions).scalar('pk', 'action')),
#             widget=form.Select2Widget(multiple=True))

#         return form_class


admin.add_view(DeploymentAdminView(models.Deployment, db.session))
admin.add_view(EventAdminView(models.Event, db.session))
admin.add_view(UserAdminView(models.User, db.session))
admin.add_view(RoleAdminView(models.Role, db.session))
