from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext.admin.form import rules
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import current_user
from ..core import admin
from .. import models


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

    def is_accessible(self):
        role = models.Role.objects.get(name='admin')
        return current_user.is_authenticated() and current_user.has_role(role)


class EventAdminView(ModelView):
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

    def is_accessible(self):
        '''For checking if the admin view is accessible.'''
        role = models.Role.objects.get(name='admin')
        return current_user.is_authenticated() and current_user.has_role(role)

    def on_model_change(self, form, model, is_created):
        # if we're creating a new event, make sure to set the
        # deployment, since it won't appear in the form
        if is_created:
            model.deployment = current_user.deployment

admin.add_view(MyView(name='Hello'))
admin.add_view(EventAdminView(models.Event))
