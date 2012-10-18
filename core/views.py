try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import itertools
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, UpdateView
import tablib
from .forms import ContactModelForm, generate_submission_form
from .models import *
from .filters import *

COMPLETION_STATUS = (
    (0, 'Complete'),
    (1, 'Partial'),
    (2, 'Empty'),
)

export_formats = ['csv', 'xls', 'xlsx', 'ods']


class TemplatePreview(TemplateView):
    page_title = ''

    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplatePreview, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.page_title = 'Dashboard'
        return super(DashboardView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class SubmissionAnalysisView(TemplateView):
    template_name = 'core/checklist_analysis.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.page_title = 'Elections Checklist Analysis'
        return super(SubmissionAnalysisView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubmissionAnalysisView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class SubmissionListView(ListView):
    context_object_name = 'submissions'
    template_name = 'core/submission_list.html'
    paginate_by = settings.PAGE_SIZE
    page_title = ''

    def get_queryset(self):
        self.page_title = self.form.name
        return self.filter_set.qs

    def get_context_data(self, **kwargs):
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.submission_filter = generate_submission_filter(self.form)
        return super(SubmissionListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.filter_set = self.submission_filter(self.request.POST,
            queryset=Submission.objects.filter(form=self.form).exclude(observer=None))
        request.session['submission_filter_%d' % self.form.pk] = self.filter_set.form.data
        return super(SubmissionListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('submission_filter_%d' % self.form.pk, None)
        self.filter_set = self.submission_filter(initial_data,
            queryset=Submission.objects.filter(form=self.form).exclude(observer=None))
        return super(SubmissionListView, self).get(request, *args, **kwargs)


class SubmissionEditView(UpdateView):
    template_name = 'core/submission_edit.html'
    page_title = 'Submission Edit'

    def get_object(self, queryset=None):
        return self.submission.master if self.submission.form.type == 'CHECKLIST' else self.submission

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.submission = get_object_or_404(Submission, pk=kwargs['pk'])
        self.form_class = generate_submission_form(self.submission.form)
        return super(SubmissionEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubmissionEditView, self).get_context_data(**kwargs)
        context['submission'] = self.submission
        context['page_title'] = self.page_title
        return context

    def get_success_url(self):
        return reverse('submissions_list', args=[self.submission.form.pk])


class ContactListView(ListView):
    context_object_name = 'contacts'
    template_name = 'core/contact_list.html'
    model = Observer
    paginate_by = settings.PAGE_SIZE
    page_title = 'Contacts List'

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ContactListView, self).dispatch(*args, **kwargs)


class ContactEditView(UpdateView):
    template_name = 'core/contact_edit.html'
    model = Observer
    form_class = ContactModelForm
    success_url = '/contacts/'
    page_title = 'Contact Edit'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ContactEditView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Observer, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(ContactEditView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


def reformat_field_name(field_name):
    return re.sub('_+', ' ', field_name).title()


def export(queryset, *args, **kwargs):
    '''Handles exporting a queryset to a StringIO instance, with its
    contents being a spreadsheet in a specified format.

    `queryset` is the queryset to be exported, the fields to be exported
    are specified as a set of positional arguments, and other arguments
    follow.

    This function requires `hstore` arguments specified as keyword
    arguments, as so:

    hstore={'data': {'position': 5, 'fields': ['AA', 'BB', 'CC']},
        'overrides': {'position': 8, 'fields': ['AB', 'BA', 'CB']}
    }

    position is the index *BEFORE* which the hstore field is inserted
    (please see list.insert() for details)

    Also, a `format` keyword argument may be specified (defaulting to 'xls')
    that specifies the format to which the spreadsheet should be exported.
    Allowed values for the `format` argument are: 'ods', 'xls', 'xlsx', 'csv'
    '''
    dataset = tablib.Dataset()

    # grab keyword arguments
    hstore_spec = kwargs.pop('hstore', None)
    format = kwargs.pop('format', 'xls')
    format = 'xls' if format not in export_formats else format

    # reorder queryset
    queryset = queryset.order_by('id')

    # grab lengths of argument 'parts'
    field_size = len(args)
    data_size = len(hstore_spec) if hstore_spec else 0

    # set various
    headers = list(args)        # headers
    all_fields = list(args)     # fields to retrieve from database

    if hstore_spec:
        # set positions for insertion
        insert_postions = [(item['position'] - field_size) for item in hstore_spec.values()]
        all_fields.extend(hstore_spec.keys())

        for item in hstore_spec.values():
            tmp = item['fields']
            pos = item['position'] - field_size

            for label in tmp:
                headers.insert(pos, label)

    dataset.headers = map(reformat_field_name, headers)

    # retrieve fields from database
    for record in queryset.values_list(*all_fields):
        # confirm if hstore fields are specified
        if data_size:
            # if so, first retrieve 'regular' fields
            row = list(record[:-data_size])

            hstore_field_spec = hstore_spec.values()

            # now, tag on each value for each hstore field, in order
            for index in range(field_size, (field_size + data_size)):            
                for key in hstore_field_spec[index - field_size]['fields']:
                    row.insert(insert_postions[index - field_size], record[index].get(key, ''))
        else:
            row = record

        dataset.append(row)

    return StringIO(getattr(dataset, format))
