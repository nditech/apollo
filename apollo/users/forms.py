# -*- coding: utf-8 -*-
from flask_babelex import gettext, lazy_gettext as _
from flask_wtf import FlaskForm
from sqlalchemy.sql import and_, exists
from wtforms import fields, validators, widgets

from apollo import constants, models, services
from apollo.frontend.forms import _make_choices
from apollo.helpers import load_source_file


class UserDetailsForm(FlaskForm):
    username = fields.StringField(_('Username'), validators=[
        validators.DataRequired()])
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
        args = [models.User.username == field.data]
        if deployment:
            args.append(models.User.deployment_id == deployment.id)
        if self.instance:
            args.append(models.User.id != self.instance.id)

        if services.users.query.filter(
            exists().where(and_(*args))
        ).scalar():
            raise validators.ValidationError(
                _('The username %(username)s is not available',
                    username=field.data))

    def validate_email(self, field):
        deployment = self.instance.deployment if self.instance else None
        args = [models.User.email == field.data]
        if deployment:
            args.append(models.User.deployment_id == deployment.id)
        if self.instance:
            args.append(models.User.id != self.instance.id)

        if services.users.query.filter(
            exists().where(and_(*args))
        ).scalar():
            raise validators.ValidationError(
                _('The email %(email)s is not available',
                    email=field.data))


def make_import_mapping_form(import_file):
    field_choices = _make_choices([
        ('username', _('Username')),
        ('email', _('Email')),
        ('password', _('Password')),
        ('role', _('Role')),
        ('lang', _('Language code')),
        ('first_name', _('First name')),
        ('last_name', _('Last name')),
    ])
    attributes = {}

    data_frame = load_source_file(import_file)
    for index, column in enumerate(data_frame.columns):
        attributes[str(index)] = fields.SelectField(
            column, choices=field_choices)

    def _validate_mappings(form: FlaskForm) -> bool:
        rv = FlaskForm.validate(form)

        errors = []
        mapped_values = form.data.values()

        if 'email' not in mapped_values:
            errors.append(
                gettext('Email was not mapped'),
            )
            rv = False
        
        form.errors['__validate__'] = errors

        return rv

    attributes['validate'] = _validate_mappings

    
    return type('UserImportMapForm', (FlaskForm,), attributes)
