from flask import redirect, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext.admin.form import rules
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import current_user
from flask.ext.security.utils import encrypt_password
from wtforms import PasswordField
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
    form_rules = [
        rules.FieldSet(
            ('name', 'logo', 'allow_observer_submission_edit'),
            _('Deployment')
        )
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.Deployment.objects(pk=user.deployment.pk)


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
    form_rules = [
        rules.FieldSet(('email', 'password', 'active', 'roles'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.User.objects(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = encrypt_password(form.password.data)

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField(_('New password'))
        return form_class


admin.add_view(DashboardView(name=_('Dashboard')))
admin.add_view(DeploymentAdminView(models.Deployment))
admin.add_view(EventAdminView(models.Event))
admin.add_view(UserAdminView(models.User))
