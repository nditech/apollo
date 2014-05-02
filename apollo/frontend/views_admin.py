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
    can_create = False
    column_list = ('name', 'start_date', 'end_date')
    column_filters = ('name', 'start_date', 'end_date')
    form_rules = [
        rules.FieldSet(('name', 'start_date', 'end_date'), _('Event'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.Event.objects(deployment=user.deployment)

    def is_accessible(self):
        role = models.Role.objects.get(name='admin')
        return current_user.is_authenticated() and current_user.has_role(role)

admin.add_view(MyView(name='Hello'))
admin.add_view(EventAdminView(models.Event))
