from .models import *
from datetime import timedelta
import django_filters
from django import forms
from django.conf import settings
from djorm_hstore.expressions import HstoreExpression


class HstoreChoiceFilter(django_filters.ChoiceFilter):
    ''' HstoreChoiceFilter is useful in filtering
    by specified values that an attribute in a Hstore field
    can contain'''
    def filter(self, qs, value):
        if value:
            # if the intent is to find records with a
            if not value == "NULL":
                return qs.where(HstoreExpression("data").contains({self.name: value}))
            else:
                return qs.where(~HstoreExpression("data").contains(self.name))
        else:
            return qs


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

    def __init__(self, *args, **kwargs):
        displayed_location_types = LocationType.objects.filter(on_display=True).values('pk', 'name')
        displayed_locations = Location.objects.filter(type__pk__in=[t['pk'] for t in displayed_location_types]) \
            .order_by('type', 'name').values('pk', 'type__name', 'name')
        filter_locations = {}
        for displayed_location in displayed_locations:
            filter_locations.setdefault(displayed_location['type__name'], [])\
                .append((displayed_location['pk'], displayed_location['name']))

        kwargs['choices'] = [["", ""]] + [[lt, filter_locations[lt]] for lt in filter_locations.keys()]
        super(LocationFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            try:
                location = Location.objects.get(pk=value)
                return qs.is_within(location)
            except Location.DoesNotExist:
                return qs.none()
        else:
            return qs


class ActivityFilter(django_filters.ChoiceFilter):
    ''' LocationFilter enables filtering of submissions
    by any of the parent locations (including the exact location)
    of the submission.
    '''

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        kwargs['choices'] = [('', 'Activity')] + list(Activity.objects.all().values_list('pk', 'name'))
        self.default_activity = request.session.get('activity', Activity.default()) if request else Activity.default()
        if self.default_activity:
            kwargs['initial'] = self.default_activity.pk
        super(ActivityFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            activity = Activity.objects.get(pk=value)
            return qs.filter(date__range=(activity.start_date, activity.end_date))
        elif self.default_activity:
            return qs.filter(date__range=(self.default_activity.start_date, self.default_activity.end_date))
        else:
            return qs


class SampleFilter(django_filters.ChoiceFilter):
    ''' LocationFilter enables filtering of submissions
    by any of the parent locations (including the exact location)
    of the submission.
    '''

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [('', 'Sample')] + list(Sample.objects.all().values_list('pk', 'name'))
        super(SampleFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value:
            try:
                sample = Sample.objects.get(pk=value)
                return qs.filter(location__pk__in=sample.locations.all().values_list('pk', flat=True))
            except Sample.DoesNotExist:
                return qs.none()
        else:
            return qs


class BaseContactsFilter(django_filters.FilterSet):
    class Meta:
        model = Observer
        fields = ['observer_id', 'name', 'role', 'location',
            'partner']

    def __init__(self, *args, **kwargs):
        super(BaseContactsFilter, self).__init__(*args, **kwargs)
        self.filters['role'].extra.update(
            {'empty_label': u'All Roles'})
        self.filters['partner'].extra.update(
            {'empty_label': u'All Partners'})
        self.filters['role'].field.widget.attrs['class'] = 'span3'
        self.filters['partner'].field.widget.attrs['class'] = 'span3'
        self.filters['name'].field.widget.attrs['class'] = 'span3'
        self.filters['name'].field.widget.attrs['placeholder'] = 'Name'
        self.filters['observer_id'].field.widget.attrs['class'] = 'span3'
        self.filters['observer_id'].field.widget.attrs['placeholder'] = 'Observer ID'


def generate_contacts_filter():
    metafields = {'model': Observer, 'fields':
        ['observer_id', 'name', 'role', 'location', 'partner']}
    metaclass = type('Meta', (), metafields)
    fields = {'Meta': metaclass}

    fields['location'] = LocationFilter(widget=forms.Select(attrs={
        'class': 'span4 input-xlarge select2',
        'data-placeholder': 'Location'}))
    return type('ContactsFilter', (BaseContactsFilter,), fields)


class BaseSubmissionFilter(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(BaseSubmissionFilter, self).__init__(*args, **kwargs)
        self.filters['activity'] = ActivityFilter(
            widget=forms.HiddenInput(),
            request=request)


def generate_submission_filter(form):
    metafields = {'model': Submission, 'fields':
        ['observer__observer_id', 'date', 'location', 'activity']}
    for group in form.groups.all():
        metafields['fields'].append('group_%d' % (group.pk,))

    if form.type == 'INCIDENT':
        # add the status filter option
        metafields['fields'].append('status')

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

    fields['location'] = LocationFilter(widget=forms.Select(attrs={
        'class': 'span4 input-xlarge select2',
        'data-placeholder': 'Location'}))
    fields['activity'] = ActivityFilter(widget=forms.HiddenInput())

    if form.type == 'INCIDENT':
        fields['status'] = HstoreChoiceFilter(
            widget=forms.Select(attrs={'class': 'span2'}), label='Status',
            choices=(('', 'Status'), ('NULL', 'Unmarked'), ('confirmed', 'Confirmed'),
                ('rejected', 'Rejected')))
    return type('SubmissionFilter', (BaseSubmissionFilter,), fields)


class LocationsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = Location
        fields = ['name', 'type']

    def __init__(self, *args, **kwargs):
        super(LocationsFilter, self).__init__(*args, **kwargs)
        self.filters['type'].extra.update(
            {'empty_label': 'All Location Types'})
        self.filters['name'].field.widget.attrs['class'] = 'span3'
        self.filters['name'].field.widget.attrs['placeholder'] = 'Name'
        self.filters['type'].field.widget.attrs['class'] = 'span3'


class DashboardFilter(django_filters.FilterSet):
    location = LocationFilter(widget=forms.Select(attrs={
        'class': 'span4 input-xlarge select2',
        'data-placeholder': 'Location'}))
    activity = ActivityFilter(widget=forms.Select(attrs={'class': 'span3'}))
    sample = SampleFilter(widget=forms.Select(attrs={'class': 'span2'}))

    class Meta:
        model = Submission
        fields = ['location', 'activity', 'sample']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(DashboardFilter, self).__init__(*args, **kwargs)
        self.filters['activity'] = ActivityFilter(
            widget=forms.HiddenInput(),
            request=request)


class SubmissionsAnalysisFilter(django_filters.FilterSet):
    sample = SampleFilter(widget=forms.Select(attrs={'class': 'span2'}))
    activity = ActivityFilter(widget=forms.HiddenInput())

    class Meta:
        model = Submission
        fields = ['sample']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(SubmissionsAnalysisFilter, self).__init__(*args, **kwargs)
        self.filters['activity'] = ActivityFilter(
            widget=forms.HiddenInput(),
            request=request)
