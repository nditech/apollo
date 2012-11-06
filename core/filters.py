from .models import *
import django_filters
from django import forms


class FormGroupFilter(django_filters.ChoiceFilter):
    ''' FormGroupFilter enables filtering of submissions
    by group completion status - complete, missing or partial
    groups are named: group_1 where 1 is the primary key or id
    of the group in consideration.
    '''
    def filter(self, qs, value):
        group = FormGroup.objects.get(pk=int(self.name.split('_')[1]))

        # is_partial?
        if value == '1':
            return qs.is_partial(group)

        # is_missing?
        elif value == '2':
            return qs.is_missing(group)

        # is_complete?
        elif value == '3':
            return qs.is_complete(group)
        else:
            return qs


class LocationFilter(django_filters.ChoiceFilter):
    ''' LocationFilter enables filtering of submissions
    by any of the parent locations (including the exact location)
    of the submission.
    '''
    def filter(self, qs, value):
        if value:
            try:
                location = Location.objects.get(pk=value)
                return qs.is_within(location)
            except Location.DoesNotExist:
                return qs.none()
        else:
            return qs


class BaseSubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = Submission
        fields = ['observer__observer_id', 'date', 'location']


def generate_submission_filter(form):
    metafields = {'model': Submission, 'fields':
        ['observer__observer_id', 'date', 'location']}
    for group in form.groups.all():
        metafields['fields'].append('group_%d' % (group.pk,))

    metaclass = type('Meta', (), metafields)
    fields = {'Meta': metaclass}
    for group in form.groups.all():
        CHOICES = [
            ('0', '%s Status' % group.name),
            ('1', '%s Partial' % group.name),
            ('2', '%s Missing' % group.name),
            ('3', '%s Complete' % group.name)
            ]
        fields['group_%d' % (group.pk,)] = FormGroupFilter(label=group.name,
            choices=CHOICES, widget=forms.Select(attrs={'class': 'span2'}))
    fields['observer__observer_id'] = django_filters.CharFilter(widget=forms.TextInput(attrs={
        'class': 'span2',
        'placeholder': 'Observer ID'
        }))

    displayed_location_types = LocationType.objects.filter(on_display=True).values('pk', 'name')
    displayed_locations = Location.objects.filter(type__in=[t['pk'] for t in displayed_location_types]) \
        .order_by('type', 'name').values('pk', 'type__name', 'name')
    filter_locations = {}
    for displayed_location in displayed_locations:
        filter_locations.setdefault(displayed_location['type__name'], [])\
            .append((displayed_location['pk'], displayed_location['name']))
    fields['location'] = LocationFilter(widget=forms.Select(attrs={
        'class': 'span4 input-xlarge select2',
        'data-placeholder': 'Location'}),
        choices=[["", ""]] + [[lt, filter_locations[lt]] for lt in filter_locations.keys()])
    return type('SubmissionFilter', (BaseSubmissionFilter,), fields)
