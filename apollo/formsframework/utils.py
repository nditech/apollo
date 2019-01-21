# -*- coding: utf-8 -*-
import logging
import re

from pyxform import xls2json
from pyxform.errors import PyXFormError
from slugify import slugify_unicode
from unidecode import unidecode
from xlwt import Workbook

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
            if field_dict.get('extra') == 'comment':
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
            if field_dict.get('extra') == 'category':
                field['type'] = 'category'
            else:
                field['type'] = 'select'

        # multiple-choice
        elif record_type.startswith('select'):
            field['type'] = 'multiselect'

        elif record_type == 'geopoint':
            field['type'] = 'location'
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


def export_form(form):
    book = Workbook()

    # set up worksheets
    survey_sheet = book.add_sheet('survey')
    choices_sheet = book.add_sheet('choices')
    analysis_sheet = book.add_sheet('analysis')
    metadata_sheet = book.add_sheet('metadata')

    if form.form_type == 'CHECKLIST' and form.quality_checks_enabled:
        qa_sheet = book.add_sheet('quality_checks')
    else:
        qa_sheet = None

    # set up headers
    survey_header = ['type', 'name', 'label', 'constraints', 'extra']
    choices_header = ['list name', 'name', 'label']
    analysis_header = ['name', 'analysis']
    metadata_header = ['name', 'prefix', 'form_type',
                       'require_exclamation', 'calculate_moe',
                       'accredited_voters_tag', 'invalid_votes_tag',
                       'registered_voters_tag', 'blank_votes_tag',
                       'quality_checks_enabled']
    qa_header = ['description', 'left', 'relation', 'right']

    # output headers
    for col, value in enumerate(survey_header):
        survey_sheet.write(0, col, value)
    for col, value in enumerate(choices_header):
        choices_sheet.write(0, col, value)
    for col, value in enumerate(analysis_header):
        analysis_sheet.write(0, col, value)
    for col, value in enumerate(metadata_header):
        metadata_sheet.write(0, col, value)
    if qa_sheet:
        for col, value in enumerate(qa_header):
            qa_sheet.write(0, col, value)

    # fill out form properties
    metadata_sheet.write(1, 0, form.name)
    metadata_sheet.write(1, 1, form.prefix)
    metadata_sheet.write(1, 2, form.form_type.code)
    metadata_sheet.write(1, 3, 1 if form.require_exclamation else 0)
    metadata_sheet.write(1, 4, 1 if form.calculate_moe else 0)
    metadata_sheet.write(1, 5, form.accredited_voters_tag)
    metadata_sheet.write(1, 6, form.invalid_votes_tag)
    metadata_sheet.write(1, 7, form.registered_voters_tag)
    metadata_sheet.write(1, 8, form.blank_votes_tag)
    metadata_sheet.write(1, 9, 1 if form.quality_checks_enabled else 0)

    # write out form structure
    current_survey_row = 1
    current_choices_row = 1
    current_analysis_row = 1
    groups = form.data.get('groups')
    if groups and isinstance(groups, list):
        boolean_written = False
        current_group = None
        for group in groups:
            if not group:
                continue

            if current_group:
                current_group = group
                survey_sheet.write(current_survey_row, 0, 'end group')
                current_survey_row += 1
            survey_sheet.write(current_survey_row, 0, 'begin group')
            survey_sheet.write(
                current_survey_row, 1, slugify_unicode(group['name']))
            survey_sheet.write(current_survey_row, 2, group['name'])
            current_survey_row += 1
            current_group = group

            fields = group.get('fields')
            if fields and isinstance(fields, list):
                for field in fields:
                    # output the type
                    if field['type'] == 'integer':
                        survey_sheet.write(
                            current_survey_row, 0, 'integer')
                        survey_sheet.write(
                            current_survey_row, 3,
                            '. >= {} and . <= {}'.format(
                                field.get('min', 0),
                                field.get('max', 9999)))
                    elif field['type'] == 'boolean':
                        survey_sheet.write(
                            current_survey_row, 0, 'select_one boolean')

                        # write out boolean choices if they haven't been
                        # written before
                        if not boolean_written:
                            choices_sheet.write(
                                current_choices_row, 0, 'boolean')
                            choices_sheet.write(current_choices_row, 1, 0)
                            choices_sheet.write(
                                current_choices_row, 2, 'False')
                            current_choices_row += 1
                            choices_sheet.write(
                                current_choices_row, 0, 'boolean')
                            choices_sheet.write(current_choices_row, 1, 1)
                            choices_sheet.write(
                                current_choices_row, 2, 'True')
                            boolean_written = True

                    elif field['type'] in ('comment', 'string'):
                        survey_sheet.write(current_survey_row, 0, 'text')
                        if field['type'] == 'comment':
                            survey_sheet.write(
                                current_survey_row, 4, 'comment')
                    elif field['type'] == 'location':
                        survey_sheet.write(current_survey_row, 0, 'geopoint')
                    else:
                        # for questions with choices, write them to the
                        # choices sheet
                        option_list_name = '{}_options'.format(
                            field['tag'])
                        options = field.get('options')
                        for description, value in options.items():
                            choices_sheet.write(
                                current_choices_row, 0, option_list_name)
                            choices_sheet.write(
                                current_choices_row, 1, value)
                            choices_sheet.write(
                                current_choices_row, 2, description)
                            current_choices_row += 1

                        if field['type'] in ('category', 'select'):
                            survey_sheet.write(
                                current_survey_row, 0,
                                'select_one {}'.format(option_list_name))
                            if field['type'] == 'category':
                                survey_sheet.write(
                                    current_survey_row, 4, 'category')
                        else:
                            survey_sheet.write(
                                current_survey_row, 0,
                                'select_multiple {}'.format(
                                    option_list_name))

                    # output the name and description
                    survey_sheet.write(current_survey_row, 1, field['tag'])
                    survey_sheet.write(
                        current_survey_row, 2, field['description'])
                    current_survey_row += 1

                    # also output the analysis
                    analysis_sheet.write(
                        current_analysis_row, 0, field['tag'])
                    analysis_sheet.write(
                        current_analysis_row, 1, field['analysis_type'])
                    current_analysis_row += 1

        if current_group:
            survey_sheet.write(current_survey_row, 0, 'end group')

    quality_checks = form.quality_checks
    if quality_checks and qa_sheet:
        for row, check in enumerate(quality_checks, 1):
            qa_sheet.write(row, 0, check['description'])
            qa_sheet.write(row, 1, check['lvalue'])
            qa_sheet.write(row, 2, check['comparator'])
            qa_sheet.write(row, 3, check['rvalue'])

    return book
