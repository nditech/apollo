from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
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
    context_object_name = 'submission_list'
    template_name = 'core/sub_list.html'
    paginate_by = settings.SUBMISSIONS_PER_PAGE
    queryset = Submission.objects.all()
