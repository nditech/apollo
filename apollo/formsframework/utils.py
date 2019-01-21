# -*- coding: utf-8 -*-
import logging
import re

from pyxform import xls2json
from pyxform.errors import PyXFormError
from slugify import slugify_unicode
from unidecode import unidecode

from apollo.formsframework.models import Form

gt_constraint_regex = re.compile('(?:.*\.\s*\>={0,1}\s*)(\d+)')
lt_constraint_regex = re.compile('(?:.*\.\s*\<={0,1}\s*)(\d+)')

logger = logging.getLogger(__name__)


def _make_form_instance(metadata):
    form = Form()
    form.name = metadata.get('name')
    form.prefix = metadata.get('prefix')
    form.form_type = metadata.get('form_type')
    form.accredited_voters_tag = metadata.get('accredited_voters_tag')
    form.blank_votes_tag = metadata.get('blank_votes_tag')
    form.invalid_votes_tag = metadata.get('invalid_votes_tag')
    form.registered_voters_tag = metadata.get('registered_voters_tag')

    try:
        form.calculate_moe = bool(int(metadata.get('calculate_moe')))
    except ValueError:
        form.calculate_moe = False
    try:
        form.quality_checks_enabled = bool(
            int(metadata.get('quality_checks_enabled')))
    except ValueError:
        form.quality_checks_enabled = False
    try:
        form.require_exclamation = bool(
            int(metadata.get('require_exclamation')))
    except ValueError:
        form.require_exclamation = False

    return form


def _process_survey_worksheet(sheet_data, form_data):
    current_group = None
    for field_dict in sheet_data:
        if field_dict['type'] == 'begin group':
            current_group = {
                'name': field_dict['label'],
                'slug': unidecode(slugify_unicode(field_dict['name'])),
                'fields': []
            }
            form_data['groups'].append(current_group)
            continue

        if 'name' not in field_dict:
            continue

        record_type = field_dict['type']
        field = {
            'tag': field_dict['name'],
            'description': field_dict['label'],
            'analysis_type': 'N/A'
        }

        # integer
        if record_type == 'integer':
            field['type'] = record_type

            # add default constraints
            field['min'] = 0
            field['max'] = 9999

            # TODO: probably a better way to handle this than
            # use regexes
            constraint_text = field_dict.get('constraints')
            if constraint_text:
                gt_match = gt_constraint_regex.match(constraint_text)
                lt_match = lt_constraint_regex.match(constraint_text)
                if gt_match:
                    try:
                        field['min'] = int(gt_match.group(1))
                    except ValueError:
                        pass

                if lt_match:
                    try:
                        field['max'] = int(lt_match.group(1))
                    except ValueError:
                        pass

        # text
        elif record_type == 'text':
            if field_dict['extra'] == 'comment':
                field['type'] = 'comment'
            else:
                field['type'] = 'string'

        # boolean
        elif 'boolean' in record_type:
            field['type'] = 'boolean'
            field['min'] = 0
            field['max'] = 1

        # single-choice
        elif record_type.startswith('select_one'):
            if field_dict['extra'] == 'category':
                field['type'] = 'category'
            else:
                field['type'] = 'select'

        # multiple-choice
        elif record_type.startswith('select'):
            field['type'] = 'multiselect'

        else:
            continue

        current_group['fields'].append(field)
        form_data['field_cache'].update({field['tag']: field})


def _process_choices_worksheet(choices_data, form_schema):
    for option_dict in choices_data:
        if option_dict['list name'] == 'boolean':
            continue

        tag, _ = option_dict['list name'].split('_')
        field = form_schema['field_cache'][tag]
        if not field.get('options'):
            field['options'] = {}
        field['options'].update(
            {option_dict['label']: int(option_dict['name'])})


def _process_analysis_worksheet(analysis_data, form_schema):
    for analysis_dict in analysis_data:
        field = form_schema['field_cache'][analysis_dict['name']]
        field['analysis_type'] = analysis_dict['analysis']


def import_form(sourcefile):
    try:
        file_data = xls2json.xls_to_dict(sourcefile)
    except PyXFormError:
        logger.exception('Error parsing Excel schema file')

    survey_data = file_data.get('survey')
    choices_data = file_data.get('choices')
    analysis_data = file_data.get('analysis')
    metadata = file_data.get('metadata')

    if not (survey_data and metadata):
        return

    form = _make_form_instance(metadata[0])
    form.data = {'groups': [], 'field_cache': {}}

    # go over the survey worksheet
    _process_survey_worksheet(survey_data, form.data)

    # go over the options worksheet
    if choices_data:
        _process_choices_worksheet(choices_data, form.data)

    # go over the analysis worksheet
    if analysis_data:
        _process_analysis_worksheet(analysis_data, form.data)

    # remove the field cache
    form.data.pop('field_cache')
    return form
