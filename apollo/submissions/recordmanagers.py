# -*- coding: utf-8 -*-
import abc
import collections
from functools import partial
from itertools import chain, groupby
from operator import itemgetter

import six

from apollo import services
from apollo.submissions.utils import make_submission_dataframe


# ---- helpers ----
def flatten(seq):
    '''
    A modified copy of compiler.ast.flatten in Python 2.X
    (removed in Python 3). It flattens an arbitrarily nested
    sequence and drops None.
    '''
    l = []
    for element in seq:
        if isinstance(element, collections.Sequence):
            for element2 in flatten(element):
                l.append(element2)
        elif element is None:
            continue
        else:
            l.append(element)
    return l


def sum2(iterable):
    '''A clone of `sum` that has the advantage of skipping
    None if it encounters it.
    '''
    return sum(item for item in iterable if item)


def cmp(a, b):
    return (a > b) - (a < b)


def location_type_comparer(location_types, left, right):
    for location_type in location_types:
        result = cmp(left.get(location_type), right.get(location_type))

        if result != 0:
            return result

    return result


class DKANRecordManager(six.with_metaclass(abc.ABCMeta)):
    def generate_records(self, queryset, tag, location_types):
        if not queryset.count():
            return []

        form = queryset.first().form
        field = form.get_field_by_tag(tag)

        # this doesn't make sense for fields not flagged for process analysis
        if field['analysis_type'] != 'PROCESS':
            return []

        if field['is_boolean']:
            # multiselect field
            return self._generate_for_multiselect_field(queryset, field,
                                                        location_types)
        elif field.get('options'):
            # single-choice field
            return self._generate_for_single_choice_field(queryset, field,
                                                          location_types)
        else:
            return self._generate_for_numeric_field(queryset, field,
                                                    location_types)

    @abc.abstractmethod
    def _generate_for_numeric_field(self, queryset, field, location_types):
        return

    @abc.abstractmethod
    def _generate_for_single_choice_field(self, queryset, field,
                                          location_types):
        return

    @abc.abstractmethod
    def _generate_for_multiselect_field(self, queryset, field, location_types):
        return


class AggregationFrameworkRecordManager(DKANRecordManager):
    def _generate_for_numeric_field(self, queryset, field, location_types):
        token = '${}'.format(field.name)

        project_stage = {'var': token, '_id': 0}
        project_stage.update({'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {'$match': queryset._query},
            {'$project': project_stage},
            {'$group': {
                '_id': '$location_name_path',
                'total': {'$sum': '$var'}
            }},
            {'$project': {
                '_id': 0, 'location_name_path': '$_id', 'total': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get('result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get(
                'location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(list(zip(subtypes, key)))

                row.update({
                    field.description: sum(record.get('total')
                                           for record in group)})
                records.append(row)

        headers = location_types + [field.description]

        return records, headers

    def _generate_for_single_choice_field(self, queryset, field,
                                          location_types):
        token = '${}'.format(field.name)

        # skip missing fields for the match stage
        match_query = queryset._query
        match_query.update({field.name: {'$ne': None}})

        project_stage = {'var': token, '_id': 0}
        project_stage.update({'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {'$match': match_query},
            {'$project': project_stage},
            {'$group': {
                '_id': {
                    'location_name_path': '$location_name_path',
                    'option': '$var'
                },
                'count': {'$sum': 1}
            }},
            {'$group': {
                '_id': '$_id.location_name_path',
                'options': {
                    '$push': {'option': '$_id.option', 'count': '$count'}
                }
            }},
            {'$project': {
                '_id': 0,
                'location_name_path': '$_id',
                'options': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get('result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get('location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(list(zip(subtypes, key)))

                group_options = [i.get('options') for i in group]

                for description, option in list(field.options.items()):
                    row['{} | {}'.format(field.description, description)] = \
                        sum(r.get('count') for r in chain.from_iterable(group_options) if r.get('option') == option)

                records.append(row)

        # headers
        sorted_options = sorted(list(field.options.items()), key=itemgetter(1))
        headers = location_types + [
            '{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers

    def _generate_for_multiselect_field(self, queryset, field, location_types):
        token = '${}'.format(field.name)

        # skip missing fields for the match stage
        match_query = queryset._query
        match_query.update({field.name: {'$ne': None}})

        project_stage = {'var': token, '_id': 0}
        project_stage.update({'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {'$match': match_query},
            {'$unwind': token},
            {'$project': project_stage},
            {'$group': {
                '_id': {
                    'location_name_path': '$location_name_path',
                    'option': '$var'
                },
                'count': {'$sum': 1}
            }},
            {'$group': {
                '_id': '$_id.location_name_path',
                'options': {
                    '$push': {'option': '$_id.option', 'count': '$count'}
                }
            }},
            {'$project': {
                '_id': 0,
                'location_name_path': '$_id',
                'options': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get('result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get('location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(list(zip(subtypes, key)))

                group_options = [i.get('options') for i in group]

                for description, option in list(field.options.items()):
                    row['{} | {}'.format(field.description, description)] = \
                        sum(r.get('count') for r in chain.from_iterable(group_options) if r.get('option') == option)

                records.append(row)

        # headers
        sorted_options = sorted(list(field.options.items()), key=itemgetter(1))
        headers = location_types + [
            '{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers


class PandasRecordManager(DKANRecordManager):
    def _generate_for_numeric_field(self, queryset, field, location_types):
        dataframe = make_submission_dataframe(queryset)
        records = []
        for i in range(len(location_types)):
            ltypes_subset = location_types[:i + 1]
            grouped_data = dataframe.groupby(ltypes_subset)
            for name, group in grouped_data:
                if isinstance(name, str):
                    row = {ltypes_subset[0]: name}
                else:
                    row = dict(list(zip(ltypes_subset, name)))

                row[field['description']] = int(group[field['tag']].fillna(0).sum())
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        headers = location_types + [field['description']]

        return records, headers

    def _generate_for_single_choice_field(self, queryset, field,
                                          location_types):
        dataframe = make_submission_dataframe(queryset)
        records = []
        for i in range(len(location_types)):
            ltypes_subset = location_types[:i + 1]
            grouped_data = dataframe.groupby(ltypes_subset)
            for name, group in grouped_data:
                if isinstance(name, six.string_types):
                    row = {ltypes_subset[0]: name}
                else:
                    row = dict(list(zip(ltypes_subset, name)))
                value_counts = group[field['tag']].value_counts().to_dict()
                for description, option in field['options'].items():
                    row['{} | {}'.format(field['description'], description)] = \
                                        value_counts.get(option, 0)
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        sorted_options = sorted(field['options'].items(), key=itemgetter(1))
        headers = location_types + [
            '{0} | {1}'.format(
                field['description'], s_opt[0]) for s_opt in sorted_options]

        return records, headers

    def _generate_for_multiselect_field(self, queryset, field,
                                        location_types):
        dataframe = make_submission_dataframe(queryset)
        records = []
        for i in range(len(location_types)):
            ltypes_subset = location_types[:i + 1]
            grouped_data = dataframe.groupby(ltypes_subset)
            for name, group in grouped_data:
                if isinstance(name, six.string_types):
                    row = {ltypes_subset[0]: name}
                else:
                    row = dict(zip(ltypes_subset, name))
                counter = collections.Counter(flatten(
                            group[field['tag']].tolist()))
                for description, option in field['options'].items():
                    row['{} | {}'.format(field['description'], description)] = \
                            counter.get(option)
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        sorted_options = sorted(list(field['options'].items()), key=itemgetter(1))
        headers = location_types + [
            '{0} | {1}'.format(
                field['description'], s_opt[0]) for s_opt in sorted_options]

        return records, headers


class PipelineBuilder(object):
    @classmethod
    def generate_first_stage_project(cls, fields, location_types):
        '''Generates the $project clause for the aggregation pipeline.

        Basically, this clause skips all fields in submissions except
        the `location_name_path` (reduced to only the specified location
        types) and any fields passed in as the second parameter.

        Args:
            - cls: this class. unused
            - fields: `apollo.formsframework.models.FormField` instances
            - location_types: names of location types

        Returns:
            A dict containing the $project clause for the pipeline.
        '''
        project_stage = {fi.name: 1 for fi in fields}
        project_stage['location_name_path'] = {
            lt: 1 for lt in location_types
        }
        project_stage['_id'] = 0

        return {'$project': project_stage}

    @classmethod
    def generate_first_stage_group(cls, fields):
        '''Generates the (complex) $group clause for the aggregation pipeline.

        This method delegates the actual work to other methods based on each
        field typeand just aggregates the combined result for all the fields.

        Args:
            - cls: this class.
            - fields: `apollo.formsframework.models.FormField` instances

        Returns:
            A dict with the $group clause for the pipeline.
        '''
        group_expression = {'_id': '$location_name_path'}

        for field in fields:
            if field.analysis_type != 'PROCESS':
                continue
            if not field.options:
                group_expression.update(
                    cls._numeric_field_first_stage_group(field))
            elif field.options and not field.allows_multiple_values:
                group_expression.update(
                    cls._single_choice_field_first_stage_group(field))
            else:
                group_expression.update(
                    cls._multiple_choice_field_first_stage_group(field))

        return {'$group': group_expression}

    @classmethod
    def _numeric_field_first_stage_group(cls, field):
        '''
        Generates a $group expression for a numeric field for the pipeline.

        For numeric fields, the expression is pretty simple: sum all
        the values for the entire group.

        Args:
            - cls: this class. unused
            - field: an `apollo.formsframework.models.FormField` instance

        Returns:
            A $group expression as a dict
        '''
        token = '${0}'.format(field.name)
        expression = {field.name: {'$sum': token}}

        return expression

    @classmethod
    def _single_choice_field_first_stage_group(cls, field):
        '''
        Generates a $group expression for a single-choice field for the
        pipeline.

        For single-choice fields, for each valid option, $push 1 or 0
        to a field named <field_name>__<option>, depending on whether
        that value was encounted or not. So a field named AA with options
        [1-3] would have three fields generated: AA_1, AA_2, AA_3, and
        each of them would be a list of 1s and 0s, depending on whether
        such an option was found or not.

        Args:
            - cls: this class. unused.
            - field: an `apollo.formsframework.models.FormField` instance

        Returns:
            A $group expression as a dict
        '''
        token = '${0}'.format(field.name)
        expression = {
            '{0}_{1}'.format(field.name, val): {
                '$push': {'$cond': [{'$eq': [token, val]}, 1, 0]}
            }
            for val in list(field.options.values())}

        return expression

    @classmethod
    def _multiple_choice_field_first_stage_group(cls, field):
        '''
        Generates a $group expression for a multiple-choice field for
        the pipeline.

        For multiple-choice fields, $push all values (which should be a list
        with values equal to valid options) to a field with the same name,
        except if the field is null, in which case, push an empty list
        (so when we're completing the aggregation in Python, we don't
        deal with None and choke).

        Args:
            - cls: this class. unused.
            - field: an `apollo.formsframework.models.FormField` instance

        Returns:
            A $group expression as a dict
        '''
        token = '${0}'.format(field.name)
        expression = {field.name: {'$push': {'$ifNull': [token, []]}}}

        return expression

    def __init__(self, queryset):
        self.queryset = queryset
        sample = self.queryset.first()
        self.form = sample.form

        # skip fields not used for process analysis
        self.fields = sorted(
            (self.form.get_field_by_tag(tag)
                for tag in self.form.tags
                if self.form.get_field_by_tag(
                    tag).analysis_type == 'PROCESS'),
            key=lambda fi: fi.name)
        self.location_types = [
            lt.name for lt in services.location_types.find().order_by(
                'ancestor_count')][:-1]

    def generate_pipeline(self):
        pipeline = [
            {'$match': self.queryset._query},
            self.generate_first_stage_project(
                self.fields, self.location_types),
            self.generate_first_stage_group(self.fields)
        ]

        return pipeline


class AggFrameworkExporter(object):
    def __init__(self, queryset):
        self.queryset = queryset
        if self.queryset.count() == 0:
            raise ValueError('Empty queryset specified')

        self.pipeline_builder = PipelineBuilder(queryset)

    def export_dataset(self):
        collection = self.queryset._collection
        pipeline = self.pipeline_builder.generate_pipeline()

        result = collection.aggregate(pipeline).get('result')

        # generate headers
        ltypes = self.pipeline_builder.location_types
        headers = ltypes[:]
        for field in self.pipeline_builder.fields:
            if not field.options:
                headers.append(field.name)
            else:
                headers.extend(
                    '{0}|{1}'.format(field.name, opt)
                    for opt in sorted(field.options.values()))

        # generate records
        records = []
        for index, location_type in enumerate(ltypes):
            subtypes = ltypes[:index + 1]
            sort_key = lambda rec: [rec.get('_id').get(lt) for lt in subtypes]

            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(list(zip(subtypes, key)))

                for field in self.pipeline_builder.fields:
                    # `group` is an iterator. it must be converted
                    # to a list otherwise it'll be exhausted after
                    # the first field runs (yeah, it bit me and i had
                    # a hard time until i figured it out)
                    group = list(group)
                    if field.options:
                        for opt in sorted(field.options.values()):
                            row_key = '{0}|{1}'.format(field.name, opt)
                            if field.allows_multiple_values:
                                # multiple-choice field
                                row[row_key] = sum2(collections.Counter(chain.from_iterable(r.get(field.name))).get(opt) for r in group if r.get(field.name))
                            else:
                                # single-choice field
                                row[row_key] = sum2(chain.from_iterable(r.get('{0}_{1}'.format(field.name, opt)) for r in group))
                    else:
                        # hopefully, we have a numeric field at this point
                        row[field.name] = sum2(r.get(field.name, 0) for r in group)

                records.append(row)

        return records, headers


def exporter_usage(queryset):
    import csv
    from io import StringIO

    exporter = AggFrameworkExporter(queryset)
    mybuffer = StringIO()

    records, headers = exporter.export_dataset()

    writer = csv.DictWriter(mybuffer, headers)
    writer.writeheader()

    for record in records:
        writer.writerow(record)

    # return the file for writing into a HTTP response
    return mybuffer
