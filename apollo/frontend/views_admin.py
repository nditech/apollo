import base64
from flask import redirect, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext.admin.form import rules
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import current_user
from flask.ext.security.utils import encrypt_password
import magic
from wtforms import FileField, PasswordField
from ..core import admin
from .. import models


class DashboardView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('dashboard.index'))


class BaseAdminView(ModelView):
    def is_accessible(self):
        '''For checking if the admin view is accessible.'''
        role = models.Role.objects.get(name='admin')
        return current_user.is_authenticated() and current_user.has_role(role)


class DeploymentAdminView(BaseAdminView):
    can_create = False
    can_delete = False
    column_list = ('name',)
    form_excluded_columns = ('hostnames',)
    form_rules = [
        rules.FieldSet(
            ('name', 'logo', 'allow_observer_submission_edit'),
            _('Deployment')
        )
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.Deployment.objects(pk=user.deployment.pk)

    def on_model_change(self, form, model, is_created):
        raw_data = request.files[form.logo.name].read()
        if len(raw_data) == 0:
            # hack because at this point, model has already been populated
            model_copy = models.Deployment.objects.get(pk=model.pk)
            model.logo = model_copy.logo
        mimetype = magic.from_buffer(raw_data, mime=True)

        # if we don't have a valid image, don't do anything
        if not mimetype.startswith('image'):
            return

        encoded = base64.b64encode(raw_data)
        model.logo = 'data:{};base64,{}'.format(mimetype, encoded)

    def scaffold_form(self):
        form_class = super(DeploymentAdminView, self).scaffold_form()
        form_class.logo = FileField(_('Logo'))

        return form_class


class EventAdminView(BaseAdminView):
    # disallow event creation
    # can_create = False

    # what fields to be displayed in the list view
    column_list = ('name', 'start_date', 'end_date')

    # what fields filtering is allowed by
    column_filters = ('name', 'start_date', 'end_date')

    # rules for form editing. in this case, only the listed fields
    # and the header for the field set
    form_rules = [
        rules.FieldSet(('name', 'start_date', 'end_date'), _('Event'))
    ]

    def get_query(self):
        '''Returns the queryset of the objects to list.'''
        user = current_user._get_current_object()
        return models.Event.objects(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        # if we're creating a new event, make sure to set the
        # deployment, since it won't appear in the form
        if is_created:
            model.deployment = current_user.deployment


class UserAdminView(BaseAdminView):
    '''Thanks to mrjoes and this Flask-Admin issue:
    https://github.com/mrjoes/flask-admin/issues/173
    '''
    column_list = ('email',)
    form_excluded_columns = ('password',)
    form_rules = [
        rules.FieldSet(('email', 'password2', 'active', 'roles'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.User.objects(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        if form.password2.data:
            model.password = encrypt_password(form.password.data)
        if is_created:
            model.deployment = current_user.deployment

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password2 = PasswordField(_('New password'))
        return form_class


admin.add_view(DashboardView(name=_('Dashboard')))
admin.add_view(DeploymentAdminView(models.Deployment))
admin.add_view(EventAdminView(models.Event))
admin.add_view(UserAdminView(models.User))
