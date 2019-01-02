# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from sqlalchemy.sql import and_, exists
from wtforms import fields, validators, widgets

from apollo import constants, models, services


class UserDetailsForm(FlaskForm):
    username = fields.StringField(_('Username'))
    email = fields.StringField(_('Email'), validators=[
        validators.DataRequired(), validators.Email()])
    password = fields.StringField(
        _('Password'),
        validators=[validators.EqualTo('password_confirm')],
        widget=widgets.PasswordInput())
    password_confirm = fields.StringField(
        _('Confirm Password'),
        widget=widgets.PasswordInput())
    locale = fields.SelectField(_('Language'),
                                choices=constants.LANGUAGE_CHOICES)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')

        if self.instance:
            initial_data = {
                'email': self.instance.email,
                'locale': self.instance.locale,
                'username': self.instance.username,
            }

            kwargs.update(data=initial_data)

        super().__init__(*args, **kwargs)

    def validate_username(self, field):
        deployment = self.instance.deployment if self.instance else None
        args = [models.User.username != field.data]
        if deployment:
            args.append(models.User.deployment_id == deployment.id)
        if self.instance:
            args.append(models.User.id != self.instance.id)

        if services.users.query.filter(exists().where(and_(*args))).scalar():
            raise validators.ValidationError(
                _('The username %(username)s is not available',
                  username=field.data))

    def validate_email(self, field):
        deployment = self.instance.deployment if self.instance else None
        args = [models.User.email != field.data]
        if deployment:
            args.append(models.User.deployment_id == deployment.id)
        if self.instance:
            args.append(models.User.id != self.instance.id)

        if services.users.query.filter(exists().where(and_(*args))).scalar():
            raise validators.ValidationError(
                _('The email %(email)s is not available',
                  email=field.data))
