from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import render_to_response
from .models import *


def list_submissions(queryset, page_num):
    '''Utility function to return a set of submissions from a queryset'''
    paginator = Paginator(queryset, settings.SUBMISSIONS_PER_PAGE)
    
    try:
        submissions = paginator.page(page_num)
    except PageNotAnInteger:
        # return first page if page is not an integer
        submissions = paginator.page(1)
    except EmptyPage:
        # return last page if page is out of range
        submissions = paginator.page(paginator.num_pages)

    return submissions


def submission_table_view(request, page=None):
    '''Function-based tabular view for submissions'''
