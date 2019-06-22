# -*- coding: utf-8 -*-
from datetime import datetime
from flask import flash, g, send_file, redirect, url_for, request
from flask_admin import (
    form, BaseView, expose)
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.form import rules
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.template import macro
from flask_babelex import gettext as _
from flask_security import current_user
from flask_security.utils import encrypt_password, url_for_security
from io import BytesIO
from jinja2 import contextfunction
import pytz
from slugify import slugify_unicode
from wtforms import PasswordField, SelectField, SelectMultipleField, validators
from zipfile import ZipFile, ZIP_DEFLATED

from apollo.core import admin, db
from apollo import models, services, settings
from apollo.constants import LANGUAGE_CHOICES
from apollo.deployments.serializers import EventArchiveSerializer
from apollo.locations.views_locations import (
    locations_builder, import_divisions, export_divisions,
    locations_list, location_edit, locations_import, locations_headers)


app_time_zone = pytz.timezone(settings.TIMEZONE)
utc_time_zone = pytz.utc

excluded_perm_actions = ['view_forms', 'access_event']

DATETIME_FORMAT_SPEC = '%Y-%m-%d %H:%M:%S %Z'


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

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for_security('login', next=request.url))


class ExtraDataInlineFormAdmin(InlineFormAdmin):
    form_columns = ('id', 'name', 'label', 'visible_in_lists')

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.deployment = g.deployment
            model.resource_type = model.__mapper_args__['polymorphic_identity']

    def on_model_delete(self, model):
        # if this model has a resource attached to it, delete it as well
        models.Resource.query.filter_by(uuid=model.uuid).delete()


class ExtraDataInlineFormList(InlineModelFormList):
    def __init__(self, frm, session, model, prop, inline_view, **kwargs):
        self.form = frm
        self.session = session
        self.model = model
        self.prop = prop
        self.inline_view = inline_view
        self._pk = 'id'

        form_opts = form.FormOpts(
            widget_args=getattr(inline_view, 'form_widget_args', None),
            form_rules=inline_view._form_rules)
        form_field = self.form_field_type(frm, self._pk, form_opts=form_opts)
        super(InlineModelFormList, self).__init__(form_field, **kwargs)


class LocationExtraDataModelConverter(InlineModelConverter):
    inline_field_list_type = ExtraDataInlineFormList

    def _calculate_mapping_key_pair(self, model, info):
        return (
            models.LocationSet.extra_fields.key,
            models.LocationDataField.location_set.key)


class ParticipantExtraDataModelConverter(InlineModelConverter):
    inline_field_list_type = ExtraDataInlineFormList

    def _calculate_mapping_key_pair(self, model, info):
        return (
            models.ParticipantSet.extra_fields.key,
            models.ParticipantDataField.participant_set.key)


class DeploymentAdminView(BaseAdminView):
    can_create = False
    can_delete = False
    can_edit = True
    column_list = ('name', 'hostnames')
    form_edit_rules = [
        rules.FieldSet(
            (
                'name', 'allow_observer_submission_edit',
                'dashboard_full_locations',
                'enable_partial_response_for_messages', 'hostnames',
                'primary_locale', 'other_locales'
            ),
            _('Deployment')
        )
    ]

    form_columns = ['name', 'hostnames', 'dashboard_full_locations',
                    'enable_partial_response_for_messages',
                    'allow_observer_submission_edit', 'primary_locale',
                    'other_locales']

    def _on_model_change(self, form, model, is_created):
        # strip out the empty strings
        if model.primary_locale == '':
            model.primary_locale = None
        model.other_locales = [loc for loc in model.other_locales if loc != '']

    def get_query(self):
        return models.Deployment.query.filter_by(
            id=current_user.deployment.id)

    def scaffold_form(self):
        form_class = super().scaffold_form()
        # not stripping the first item for the primary locale
        # because stripping it would mean the language is
        # set to the next item if nothing is selected and
        # the choice is saved. as at this moment, the next
        # item is the choice for Arabic
        form_class.primary_locale = SelectField(
            _('Primary Language'), choices=LANGUAGE_CHOICES,
            validators=[validators.optional()])
        # stripping the first item for the other locales
        # so that we avoid the "None is not a valid choice"
        # error when it is selected by mistake
        form_class.other_locales = SelectMultipleField(
            _('Other Languages'), choices=LANGUAGE_CHOICES,
            validators=[validators.optional()])

        return form_class


class EventAdminView(BaseAdminView):
    column_filters = ('name', 'start', 'end')
    column_list = ('name', 'start', 'end', 'location_set', 'participant_set',
                   'archive')
    form_columns = ('name', 'start', 'end', 'forms', 'participant_set')
    form_rules = [
        rules.FieldSet(
            ('name', 'start', 'end', 'forms', 'participant_set'),
            _('Event'))
    ]
    column_formatters = {
        'archive': macro('event_archive'),
    }

    @expose('/download/<int:event_id>')
    def download(self, event_id):
        event = services.events.find(id=event_id).first_or_404()
        eas = EventArchiveSerializer()

        fp = BytesIO()
        with ZipFile(fp, 'w', ZIP_DEFLATED) as zf:
            eas.serialize(event, zf)

        fp.seek(0)
        fname = slugify_unicode(
            f'event archive {event.name.lower()} {datetime.utcnow().strftime("%Y %m %d %H%M%S")}')  # noqa

        return send_file(
            fp,
            attachment_filename=f'{fname}.zip',
            as_attachment=True)

    def get_one(self, pk):
        event = super(EventAdminView, self).get_one(pk)

        # convert start and end dates to app time zone
        event.start = event.start.astimezone(app_time_zone)
        event.end = event.end.astimezone(app_time_zone)
        return event

    @contextfunction
    def get_list_value(self, context, model, name):
        if name in ['start', 'end']:
            attribute = getattr(model, name, None)
            if attribute:
                return attribute.astimezone(
                    app_time_zone).strftime(DATETIME_FORMAT_SPEC)

            return attribute

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

            # add role permissions for this event
            roles = models.Role.query.filter_by(
                deployment=model.deployment).all()
            model.roles = roles

        if form.participant_set.data:
            model.location_set = form.participant_set.data.location_set

        # convert to the app time zone
        model.start = model.start.astimezone(app_time_zone)
        model.end = model.end.astimezone(app_time_zone)


class UserAdminView(BaseAdminView):
    '''Thanks to mrjoes and this Flask-Admin issue:
    https://github.com/mrjoes/flask-admin/issues/173
    '''
    column_list = ('email', 'roles', 'active')
    column_searchable_list = ('email',)
    form_columns = (
        'email', 'username', 'active', 'roles', 'permissions', 'locale')
    form_excluded_columns = ('password', 'confirmed_at', 'login_count',
                             'last_login_ip', 'last_login_at',
                             'current_login_at', 'deployment',
                             'current_login_ip', 'submission_comments')
    form_rules = [
        rules.FieldSet(('email', 'username', 'password2', 'active', 'roles',
                        'permissions', 'locale'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.User.query.filter_by(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        if form.password2.data:
            model.password = encrypt_password(form.password2.data)
        if is_created:
            model.deployment = current_user.deployment
        if not form.locale.data:
            model.locale = None

    def create_form(self, obj=None):
        form = super().create_form(obj)

        deployment = current_user.deployment

        # local function helper
        def _get_deployment_roles():
            return models.Role.query.filter_by(deployment_id=deployment.id)

        form.roles.query_factory = _get_deployment_roles

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        deployment = current_user.deployment

        # local function helper
        def _get_deployment_roles():
            return models.Role.query.filter_by(deployment_id=deployment.id)

        form.roles.query_factory = _get_deployment_roles

        return form

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password2 = PasswordField(_('New password'))
        form_class.locale = SelectField(
            _('Language'), choices=LANGUAGE_CHOICES)
        return form_class

    @action('disable', _('Disable'),
            _('Are you sure you want to disable the selected users?'))
    def action_disable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = False
            role.save()
        flash(_('User(s) successfully disabled.'), 'success')

    @action('enable', _('Enable'),
            _('Are you sure you want to enable the selected users?'))
    def action_enable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = True
            role.save()
        flash(_('User(s) successfully enabled.'), 'success')


class RoleAdminView(BaseAdminView):
    can_delete = False
    column_list = ('name', 'description')
    form_columns = ('name', 'description', 'permissions', 'resources')

    def create_form(self, obj=None):
        deployment = g.deployment
        form = super().create_form(obj)
        form.resources.query = models.Resource.query.filter_by(
            deployment=deployment)

        return form

    def edit_form(self, obj=None):
        deployment = g.deployment
        form = super().edit_form(obj)
        form.resources.query = models.Resource.query.filter_by(
            deployment=deployment)

        return form

    def get_one(self, pk):
        deployment = current_user.deployment
        return models.Role.query.filter_by(
            deployment_id=deployment.id, id=pk).first_or_404()


class SetViewMixin(object):
    column_filters = ('name',)

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.deployment_id = current_user.deployment.id
        super().on_model_change(form, model, is_created)


class LocationSetAdminView(SetViewMixin, BaseAdminView):
    column_list = ('name', 'administrative_divisions', 'locations')
    column_formatters = {
        'administrative_divisions': macro('locations_builder'),
        'locations': macro('locations_list'),
    }
    form_columns = ('name',)
    inline_models = (ExtraDataInlineFormAdmin(models.LocationDataField),)
    inline_model_form_converter = LocationExtraDataModelConverter

    def on_model_delete(self, model):
        # delete dependent objects first
        models.LocationPath.query.filter_by(location_set=model).delete()
        models.Location.query.filter_by(location_set=model).delete()
        models.LocationTypePath.query.filter_by(location_set=model).delete()
        models.LocationType.query.filter_by(location_set=model).delete()
        return super().on_model_delete(model)

    @expose('/builder/<int:location_set_id>', methods=['GET', 'POST'])
    def builder(self, location_set_id):
        return locations_builder(self, location_set_id)

    @expose('/builder/<int:location_set_id>/import', methods=['POST'])
    def import_divisions(self, location_set_id):
        return import_divisions(location_set_id)

    @expose('/builder/<int:location_set_id>/export')
    def export_divisions(self, location_set_id):
        return export_divisions(location_set_id)

    @expose('/locations/<int:location_set_id>')
    def locations_list(self, location_set_id):
        return locations_list(self, location_set_id)

    @expose('/locations/<int:location_set_id>/import', methods=['POST'])
    def locations_import(self, location_set_id):
        return locations_import(location_set_id)

    @expose(
        '/locations/<int:location_set_id>/headers/<int:upload_id>',
        methods=['GET', 'POST']
    )
    def locations_headers(self, location_set_id, upload_id):
        return locations_headers(self, location_set_id, upload_id)


class ParticipantSetAdminView(SetViewMixin, BaseAdminView):
    column_list = ('name', 'location_set', 'participants')
    form_columns = ('name', 'location_set',)
    column_formatters = {
        'participants': macro('participants_list')
    }
    inline_models = (ExtraDataInlineFormAdmin(models.ParticipantDataField),)
    inline_model_form_converter = ParticipantExtraDataModelConverter

    def create_form(self, obj=None):
        deployment = g.deployment
        form = super().create_form(obj)
        form.location_set.choices = models.LocationSet.query.filter_by(
            deployment=deployment).with_entities(
                models.LocationSet.id, models.LocationSet.name).all()

        return form

    def edit_form(self, obj=None):
        deployment = g.deployment
        form = super().edit_form(obj)
        form.location_set.choices = models.LocationSet.query.filter_by(
            deployment=deployment).with_entities(
                models.LocationSet.id, models.LocationSet.name).all()

        return form


class FormsView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('forms.list_forms'))


admin.add_view(DeploymentAdminView(models.Deployment, db.session))
admin.add_view(
    EventAdminView(models.Event, db.session, _('Events')))
admin.add_view(UserAdminView(models.User, db.session, _('Users')))
admin.add_view(RoleAdminView(models.Role, db.session, _('Roles')))
admin.add_view(
    LocationSetAdminView(models.LocationSet, db.session, _('Location Sets')))
admin.add_view(
    ParticipantSetAdminView(
        models.ParticipantSet, db.session, _('Participant Sets')))
admin.add_view(FormsView(name="Forms", endpoint="forms_"))
