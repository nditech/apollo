try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
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
        return self.filter_set.qs.order_by('-date', 'observer__observer_id')

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
        context['location_types'] = LocationType.objects.filter(on_display=True)
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


def create_column_header(field_name):
    if ':' in field_name:
        # get the last part. it should be an alpha code
        return field_name.split('__')[-1].upper()

    return field_name.replace('__', ' ').title()


def generate_value_list(args):
    pattern = re.compile(r'^hstore:(?P<var>\w+?)__\w+$')
    value_set = set()

    for item in args:
        match = pattern.match(item)

        if match:
            value_set.add(match.group('var'))
        else:
            value_set.add(item)

    return value_set

def make_item_row(record, args):
    row = []
    pattern = re.compile(r'^hstore:(?P<dict>\w+?)__(?P<key>\w+)$')

    for item in args:
        match = pattern.match(item)

        if match:
            row.append(record[match.group('dict')].get(match.group('key'), ''))
        else:
            row.append(record[item])

    return row


def export(queryset, *args, **kwargs):
    '''Handles exporting a queryset to a (c)StringIO instance, with its
    contents being a spreadsheet in a specified format.

    `queryset` is the queryset to be exported, the fields to be exported
    are specified as a set of positional arguments, and other arguments
    follow.

    hstore arguments are positional, and are specified as such:
        'hstore:data__AA'
    in order to get the value stored with the 'AA' key in the hstore data
    field

    Also, a `format` keyword argument may be specified (defaulting to 'xls')
    that specifies the format to which the spreadsheet should be exported.
    Allowed values for the `format` argument are: 'ods', 'xls', 'xlsx', 'csv'
    '''
    dataset = tablib.Dataset()

    # grab keyword argument
    format = kwargs.pop('format', 'xls')
    format = 'xls' if format not in export_formats else format

    # set headers
    dataset.headers = map(create_column_header, args)

    # reorder queryset
    queryset = queryset.order_by('id')

    # retrieve data and build table
    fields = generate_value_list(args)
    for record in queryset.values(*fields):
        dataset.append(make_item_row(record, args))

    return StringIO(getattr(dataset, format))
