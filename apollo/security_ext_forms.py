# -*- coding: utf-8 -*-
from flask import current_app, g, session
from flask_security.forms import LoginForm
from flask_security.confirmable import requires_confirmation
from flask_security.utils import get_message, verify_and_update_password
from werkzeug.local import LocalProxy

from apollo import models

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class DeploymentLoginForm(LoginForm):
    def validate(self):
        if not super(DeploymentLoginForm, self).validate():
            participant = models.Participant.query.filter(
                models.Participant.participant_id == self.email.data.strip(),
                models.Participant.password == self.password.data.strip(),
                models.Participant.participant_set == g.event.participant_set
            ).join(models.ParticipantRole).filter(
                models.ParticipantRole.name == '$FC'
            ).first()
            if participant:
                # get the field co-ordinator user and create it if necessary
                _user = _datastore.find_user(
                    email=current_app.config.get(
                        'APOLLO_FIELD_COORDINATOR_EMAIL'))
                if not _user:
                    _role = _datastore.find_or_create_role(
                        'field-coordinator', deployment=g.deployment)
                    _user = _datastore.create_user(
                        email=current_app.config.get(
                            'APOLLO_FIELD_COORDINATOR_EMAIL'),
                        username='',
                        password='',
                        deployment=g.deployment,
                        roles=[_role])
                self.user = _datastore.get_user(current_app.config.get(
                    'APOLLO_FIELD_COORDINATOR_EMAIL'))
                session['participant'] = participant.id
                return True
            else:
                return False
        else:
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
                self.user = _datastore.find_user(**kwargs)

                if self.user:
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
