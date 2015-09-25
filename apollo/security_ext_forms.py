from flask import current_app, g
from flask.ext.security.forms import LoginForm
from flask.ext.security.confirmable import requires_confirmation
from flask.ext.security.utils import get_message, verify_and_update_password
from werkzeug.local import LocalProxy

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class DeploymentLoginForm(LoginForm):
    def validate(self):
        if not super(DeploymentLoginForm, self).validate():
            return False

        if self.email.data.strip() == '':
            self.email.errors.append(get_message('EMAIL_NOT_PROVIDED')[0])
            return False

        if self.password.data.strip() == '':
            self.password.errors.append(
                get_message('PASSWORD_NOT_PROVIDED')[0])
            return False

        self.user = _datastore.find_user(email=self.email.data,
                                         deployment=g.deployment)

        if self.user is None:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active():
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True
