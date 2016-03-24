# -*- coding: utf-8 -*-
import abc
import collections
from functools import partial
from itertools import chain, groupby
from operator import itemgetter

import six


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
        if field.analysis_type != u'PROCESS':
            return []

        if field.allows_multiple_values:
            # multiselect field
            return self._generate_for_multiselect_field(queryset, field,
                                                        location_types)
        elif field.options:
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
        token = u'${}'.format(field.name)

        project_stage = {u'var': token, u'_id': 0}
        project_stage.update({u'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {u'$match': queryset._query},
            {u'$project': project_stage},
            {u'$group': {
                u'_id': u'$location_name_path',
                u'total': {u'$sum': u'$var'}
            }},
            {u'$project': {
                u'_id': 0, u'location_name_path': u'$_id', u'total': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get(u'result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get(
                u'location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(zip(subtypes, key))

                row.update({
                    field.description: sum(record.get(u'total')
                                           for record in group)})
                records.append(row)

        headers = location_types + [field.description]

        return records, headers

    def _generate_for_single_choice_field(self, queryset, field,
                                          location_types):
        token = u'${}'.format(field.name)

        # skip missing fields for the match stage
        match_query = queryset._query
        match_query.update({field.name: {u'$ne': None}})

        project_stage = {u'var': token, u'_id': 0}
        project_stage.update({u'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {u'$match': match_query},
            {u'$project': project_stage},
            {u'$group': {
                u'_id': {
                    u'location_name_path': u'$location_name_path',
                    u'option': u'$var'
                },
                u'count': {u'$sum': 1}
            }},
            {u'$group': {
                u'_id': u'$_id.location_name_path',
                u'options': {
                    u'$push': {u'option': u'$_id.option', u'count': u'$count'}
                }
            }},
            {u'$project': {
                u'_id': 0,
                u'location_name_path': u'$_id',
                u'options': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get(u'result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get(u'location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(zip(subtypes, key))

                group_options = [i.get(u'options') for i in group]

                for description, option in field.options.items():
                    row[u'{} | {}'.format(field.description, description)] = \
                        sum(r.get(u'count') for r in chain.from_iterable(group_options) if r.get(u'option') == option)

                records.append(row)

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers

    def _generate_for_multiselect_field(self, queryset, field, location_types):
        token = u'${}'.format(field.name)

        # skip missing fields for the match stage
        match_query = queryset._query
        match_query.update({field.name: {u'$ne': None}})

        project_stage = {u'var': token, u'_id': 0}
        project_stage.update({u'location_name_path': {
            lt: 1 for lt in location_types
        }})

        pipeline = [
            {u'$match': match_query},
            {u'$unwind': token},
            {u'$project': project_stage},
            {u'$group': {
                u'_id': {
                    u'location_name_path': u'$location_name_path',
                    u'option': u'$var'
                },
                u'count': {u'$sum': 1}
            }},
            {u'$group': {
                u'_id': u'$_id.location_name_path',
                u'options': {
                    u'$push': {u'option': u'$_id.option', u'count': u'$count'}
                }
            }},
            {u'$project': {
                u'_id': 0,
                u'location_name_path': u'$_id',
                u'options': 1
            }}
        ]

        collection = queryset._collection
        result = collection.aggregate(pipeline).get(u'result')
        records = []

        for index, location_type in enumerate(location_types):
            subtypes = location_types[:index + 1]
            sort_key = lambda rec: [rec.get(u'location_name_path').get(lt) for lt in subtypes]
            for key, group in groupby(sorted(result, key=sort_key), sort_key):
                row = dict(zip(subtypes, key))

                group_options = [i.get(u'options') for i in group]

                for description, option in field.options.items():
                    row[u'{} | {}'.format(field.description, description)] = \
                        sum(r.get(u'count') for r in chain.from_iterable(group_options) if r.get(u'option') == option)

                records.append(row)

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers


class PandasRecordManager(DKANRecordManager):
    def _generate_for_numeric_field(self, queryset, field, location_types):
        dataframe = queryset.to_dataframe()
        records = []
        for i in range(len(location_types)):
            ltypes_subset = location_types[:i + 1]
            grouped_data = dataframe.groupby(ltypes_subset)
            for name, group in grouped_data:
                if isinstance(name, six.string_types):
                    row = {ltypes_subset[0]: name}
                else:
                    row = dict(zip(ltypes_subset, name))

                row[field.description] = int(group[field.name].fillna(0).sum())
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        headers = location_types + [field.description]

        return records, headers

    def _generate_for_single_choice_field(self, queryset, field,
                                          location_types):
        dataframe = queryset.to_dataframe()
        records = []
        for i in range(len(location_types)):
            ltypes_subset = location_types[:i + 1]
            grouped_data = dataframe.groupby(ltypes_subset)
            for name, group in grouped_data:
                if isinstance(name, six.string_types):
                    row = {ltypes_subset[0]: name}
                else:
                    row = dict(zip(ltypes_subset, name))
                value_counts = group[field.name].value_counts().to_dict()
                for description, option in field.options.items():
                    row[u'{} | {}'.format(field.description, description)] = \
                                        value_counts.get(option, 0)
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers

    def _generate_for_multiselect_field(self, queryset, field,
                                        location_types):
        dataframe = queryset.to_dataframe()
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
                            group[field.name].tolist()))
                for description, option in field.options.items():
                    row[u'{} | {}'.format(field.description, description)] = \
                            counter.get(option)
                records.append(row)

        # sort
        comparer = partial(location_type_comparer, location_types)
        records = sorted(records, cmp=comparer)

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                field.description, s_opt[0]) for s_opt in sorted_options]

        return records, headers
