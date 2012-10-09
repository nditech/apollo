from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, FormView
from .forms import ContactForm
from .models import *

COMPLETION_STATUS = (
    (0, 'Complete'),
    (1, 'Partial'),
    (2, 'Empty'),
)


class TemplatePreview(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)


class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)


class SubmissionListView(ListView):
    context_object_name = 'submissions'
    template_name = 'core/submission_list.html'
    paginate_by = settings.PAGE_SIZE

    def get_queryset(self):
        return Submission.objects.filter(form__pk=self.kwargs['form']).exclude(observer=None)

    def get_context_data(self, **kwargs):
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        context['form'] = Form.objects.get(pk=self.kwargs['form'])
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SubmissionListView, self).dispatch(*args, **kwargs)


class SubmissionEditView(FormView):
    pass


class ContactListView(ListView):
    context_object_name = 'contacts'
    template_name = 'core/contact_list.html'
    model = Observer
    paginate_by = settings.PAGE_SIZE

    def get_context_data(self, **kwargs):
        return super(ContactListView, self).get_context_data(**kwargs)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ContactListView, self).dispatch(*args, **kwargs)


class ContactEditView(FormView):
    template_name = 'core/contact_edit.html'
    form_class = ContactForm
    success_url = '/contacts/'

    def form_valid(self, form):
        pass
    pass
