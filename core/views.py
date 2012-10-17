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
        return Submission.objects.filter(form=self.form).exclude(observer=None)

    def get_context_data(self, **kwargs):
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        return super(SubmissionListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


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
    follow
    '''
    dataset = tablib.Dataset()

    # grab keyword arguments
    hstore_spec = kwargs.pop('hstore', None)
    format = kwargs.pop('format', 'xls')
    format = 'xls' if format not in export_formats else format

    # reorder queryset
    queryset = queryset.order_by('id')

    # set headers
    headers = list(args)
    if hstore_spec:
        headers.extend(itertools.chain.from_iterable(hstore_spec.values()))

    dataset.headers = map(reformat_field_name, headers)

    # grab lengths of argument 'parts'
    field_size = len(args)
    data_size = len(hstore_spec) if hstore_spec else 0

    # set fields to retrieve
    all_fields = list(args)
    all_fields.extend(hstore_spec.keys())

    # retrieve fields from database
    for record in queryset.values_list(*all_fields):
        # confirm if hstore fields are specified
        if data_size:
            # if so, first retrieve 'regular' fields
            row = list(record[:-data_size])

            data_keys = hstore_spec.values()

            # now, tag on each value for each hstore field, in order
            for index in range(field_size, (field_size + data_size)):
                for key in data_keys[index - field_size]:
                    row.append(record[index].get(key, ''))
        else:
            row = record

        dataset.append(row)

    return StringIO(getattr(dataset, format))
