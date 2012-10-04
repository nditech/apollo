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

class SubmissionListView(ListView):
    paginate_by = settings.SUBMISSIONS_PER_PAGE
    queryset = Submission.objects.all()
    template_name = 'core/sublist.html'

    def dispatch(self, request, *args, **kwargs):
        return super(SubmissionListView, self).dispatch(request, *args, **kwargs)


def submission_table_view(request, page=None):
    '''Function-based tabular view for submissions'''
    try:
        page_num = int(page)
    except TypeError:
        page_num = 1
    except ValueError:
        page_num = 1

    # submissions here is a Page object
    submissions = list_submissions(Submission.objects.all(), page_num)

    # get checklist completion status


class TemplatePreview(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)


class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)
