# -*- coding: utf-8 -*-
from flask import current_app, g
from flask_security.forms import LoginForm
from flask_security.confirmable import requires_confirmation
from flask_security.utils import get_message, verify_and_update_password
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

        # check by the user identity attributes defined in
        # the settings
        for identity_attribute in current_app.config.get(
                'SECURITY_USER_IDENTITY_ATTRIBUTES'):
            kwargs = {
                'deployment': g.deployment,
                identity_attribute: self.email.data
            }
            self._user = _datastore.find_user(**kwargs)

            if self._user:
                break

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
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True
