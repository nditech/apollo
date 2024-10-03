# -*- coding: utf-8 -*-
from flask import current_app, g, session
from flask_security.forms import LoginForm
from werkzeug.local import LocalProxy

from apollo import models

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


class DeploymentLoginForm(LoginForm):
    def validate(self, **kwargs):
        if not super(DeploymentLoginForm, self).validate(**kwargs):
            participant = (
                models.Participant.query.filter(
                    models.Participant.participant_id == self.username.data.strip(),
                    models.Participant.password == self.password.data.strip(),
                    models.Participant.participant_set == g.event.participant_set,
                )
                .join(models.ParticipantRole)
                .filter(models.ParticipantRole.name == "$FC")
                .first()
            )
            if participant:
                # get the field co-ordinator user and create it if necessary
                _user = _datastore.find_user(email=current_app.config.get("APOLLO_FIELD_COORDINATOR_EMAIL"))
                if not _user:
                    _role = _datastore.find_or_create_role("field-coordinator", deployment=g.deployment)
                    _user = _datastore.create_user(
                        email=current_app.config.get("APOLLO_FIELD_COORDINATOR_EMAIL"),
                        username="",
                        password="",
                        deployment=g.deployment,
                        roles=[_role],
                    )
                self.user = _datastore.get_user(current_app.config.get("APOLLO_FIELD_COORDINATOR_EMAIL"))
                session["participant"] = participant.id
                return True
            else:
                return False
        else:
            return True
