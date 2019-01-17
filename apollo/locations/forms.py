# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.fields import SelectField
from wtforms.validators import InputRequired

from apollo.deployments.utils import get_deployment_locales
from apollo.frontend.forms import _make_choices
from apollo.helpers import load_source_file


class AdminDivisionImportForm(FlaskForm):
    '''Form for processing admin division imports'''
    import_file = FileField(_('Import File'), validators=[InputRequired()])


def _validate_mappings(form):
    rv = FlaskForm.validate(form)

    errors = []
    location_set = form.location_set
    mapped_values = form.data.values()

    for location_type in location_set.location_types:
        str_id = str(location_type.id)
        lt_values = [v for v in mapped_values if v.startswith(str_id)]

        if lt_values:
            if '{}_code'.format(location_type.id) not in lt_values:
                errors.append(
                    str(_('Properties for %(loc_type_name)s were mapped, but no code was specified',
                        loc_type_name=location_type.name)))
                rv = False

    form.errors['__validate__'] = errors

    return rv


def make_import_mapping_form(import_file, location_set):
    attributes = {'location_set': location_set, 'validate': _validate_mappings}
    map_choices = _make_choices(location_set.get_import_fields().items())

    locale_choices = get_deployment_locales(location_set.deployment_id)

    data_frame = load_source_file(import_file)
    for index, column in enumerate(data_frame.columns):
        attributes[str(index)] = SelectField(column, choices=map_choices)

    attributes['locale'] = SelectField(
        _('Language'), choices=locale_choices, validators=[InputRequired()])

    return type('LocationImportMapForm', (FlaskForm,), attributes)
