from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render_to_response
from .models import *


COMPLETION_STATUS = (
    (0, 'Complete'),
    (1, 'Partial'),
    (2, 'Empty'),
)

def list_submissions(queryset, page_num):
    '''Utility function to return a set of submissions from a queryset'''
    paginator = Paginator(queryset, settings.SUBMISSIONS_PER_PAGE)

    try:
        submissions = paginator.page(page_num)
    except EmptyPage:
        # return last page if page is out of range
        submissions = paginator.page(paginator.num_pages)

    return submissions


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
