# -*- coding: utf-8 -*-
import abc
import collections
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
                row[field.description] = int(group[field.name].sum())
                records.append(row)

        # sort
        records = sorted(records,
                         key=lambda d: (d.get(lt) for lt in location_types))

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
                                        value_counts.get(option)
                records.append(row)

        # sort
        records = sorted(records,
                         key=lambda d: (d.get(lt) for lt in location_types))

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                s_opt[0], s_opt[1]) for s_opt in sorted_options]

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
        records = sorted(records,
                         key=lambda d: (d.get(lt) for lt in location_types))

        # headers
        sorted_options = sorted(field.options.items(), key=itemgetter(1))
        headers = location_types + [
            u'{0} | {1}'.format(
                s_opt[0], s_opt[1]) for s_opt in sorted_options]

        return records, headers
