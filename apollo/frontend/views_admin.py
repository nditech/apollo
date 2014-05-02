from flask.ext.admin import BaseView, expose
from flask.ext.security import current_user
from ..core import admin
from ..models import Role


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

    def is_accessible(self):
        role = Role.objects.get(name='admin')
        return current_user.is_authenticated() and current_user.has_role(role)


admin.add_view(MyView(name='Hello'))
