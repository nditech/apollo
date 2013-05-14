# -*- coding: utf-8 -*-
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import re
from datetime import (date, datetime)
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site, get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.template.response import TemplateResponse
from django.utils import simplejson as json
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView, ListView, UpdateView, View, CreateView
from django.views.generic.base import TemplateResponseMixin
from jimmypage.cache import cache_page
from rapidsms.models import Connection, Backend
from guardian.decorators import permission_required
from guardian.shortcuts import get_objects_for_user
from rapidsms.router.api import send
import tablib
from .forms import ActivitySelectionForm, ContactModelForm, LocationModelForm, generate_submission_form, generate_verification_form
from .helpers import *
from .models import *
from .filters import *
from analyses.datagenerator import generate_process_data, generate_incidents_data

COMPLETION_STATUS = (
    (0, 'Complete'),
    (1, 'Partial'),
    (2, 'Empty'),
)

export_formats = ['csv', 'xls', 'xlsx', 'ods']


def set_activity(request, activity):
    request.session['activity'] = activity


def get_activity(request):
    return request.session.get('activity', Activity.default())


class TemplatePreview(TemplateView):
    page_title = ''

    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplatePreview, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class ActivitySelectionView(View, TemplateResponseMixin):
    template_name = 'core/activity_selection.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.form_class = ActivitySelectionForm
        return super(ActivitySelectionView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'params': kwargs}
        context['form'] = self.form
        return context

    def get(self, request, *args, **kwargs):
        self.form = self.form_class(request=request)
        context = self.get_context_data(**kwargs)
        # only display the activity selection form if this user has the right permissions
        if request.user.has_perm('core.view_activities'):
            return self.render_to_response(context)
        else:
            redirect_to = request.REQUEST.get('next', '')
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL

            return HttpResponseRedirect(redirect_to)

    @method_decorator(permission_required('core.view_activities'))
    def post(self, request, *args, **kwargs):
        self.form = self.form_class(request.POST, request=request)
        if self.form.is_valid():
            set_activity(request, self.form.cleaned_data['activity'])

            redirect_to = request.REQUEST.get('next', '')
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL

            return HttpResponseRedirect(redirect_to)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class DashboardView(View, TemplateResponseMixin):
    template_name = 'core/dashboard.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if 'group' in kwargs:
            self.form_group = get_object_or_404(FormGroup, pk=kwargs['group'])
            self.page_title = 'Dashboard · {}'.format(self.form_group.name)
            self.template_name = 'core/dashboard_status_breakdown.html'
        else:
            self.form_group = None
            self.page_title = 'Dashboard'
        if not request.user.has_perm('core.view_activities'):
            self.viewable_forms = get_objects_for_user(request.user, 'core.view_form', Form)
        else:
            self.viewable_forms = Form.objects.all()
        self.dashboard_filter = DashboardFilter

        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'params': kwargs}
        context['page_title'] = self.page_title
        context['filter_form'] = self.filter_set.form
        context['summary'] = generate_dashboard_summary(self.filter_set.qs, self.form_group)
        return context

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('dashboard_filter', None)
        self.filter_set = self.dashboard_filter(initial_data,
                queryset=Submission.objects.filter(form__in=self.viewable_forms).exclude(observer=None), request=request)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.filter_set = self.dashboard_filter(request.POST,
                queryset=Submission.objects.filter(form__in=self.viewable_forms).exclude(observer=None), request=request)
        request.session['dashboard_filter'] = self.filter_set.form.data
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class SubmissionProcessAnalysisView(View, TemplateResponseMixin):
    template_name = 'core/checklist_summary.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_analyse', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    @method_decorator(cache_page)
    def dispatch(self, request, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.page_title = '{} Analysis'.format(self.form.name)
        self.analysis_filter = generate_submission_analysis_filter(self.form)
        if 'location_id' in kwargs:
            self.location = get_object_or_404(Location, pk=kwargs['location_id'])
        else:
            self.location = Location.root()

        if self.form.type == 'CHECKLIST':
            # checklists
            if 'tag' in kwargs:
                self.template_name = 'core/checklist_summary_breakdown.html'
                self.tags = [kwargs['tag']]
                self.display_tag = kwargs['tag']
                self.grouped = True
            else:
                self.tags = settings.PROCESS_QUESTIONS_TAGS
                self.grouped = False
            self.initial_qs = Submission.objects.filter(form=self.form, observer=None).is_within(self.location)
        else:
            # critical incidents are processed differently
            self.grouped = True
            self.template_name = 'core/critical_incidents_summary.html'
            self.initial_qs = Submission.objects.filter(form=self.form).is_within(self.location)

            # the presence of a tag indicates interest in display location of incidents
            if 'tag' in kwargs:
                self.display_tag = kwargs['tag']
                self.analysis_filter = generate_critical_incidents_location_filter(self.display_tag)
                self.template_name = 'core/critical_incidents_locations.html'
                self.page_title = '{} Analysis'.format(self.form.name)

        return super(SubmissionProcessAnalysisView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'params': kwargs}
        context['page_title'] = self.page_title
        context['filter_form'] = self.filter_set.form
        context['form'] = self.form
        context['location'] = self.location
        context['display_tag'] = self.display_tag if hasattr(self, 'display_tag') else None
        if self.form.type == 'INCIDENT':
            if context['display_tag']:
                context['form_field'] = FormField.objects.get(group__form=self.form, tag=self.display_tag)
                context['incidents'] = self.filter_set.qs
                context['incidents_markers'] = get_incident_markers(self.form, self.filter_set.qs, 'Constituency', tag=True)
            else:
                context['incidents_summary'] = generate_incidents_data(self.form, self.filter_set.qs, self.location, grouped=self.grouped)
                context['incidents_markers'] = get_incident_markers(self.form, self.filter_set.qs, 'Constituency')
        else:
            context['process_summary'] = generate_process_data(self.form, self.filter_set.qs, self.location, grouped=self.grouped, tags=self.tags)
        return context

    def get(self, request, *args, **kwargs):
        self.filter_set = self.analysis_filter(request.GET, queryset=self.initial_qs, request=request)

        if request.GET.get('export', None) and self.form.type == 'INCIDENT':
            location_types = list(LocationType.objects.filter(on_display=True).values_list('name', flat=True))
            location_type_fields = ['loc:location__{}'.format(lt.lower()) for lt in location_types]
            data_fields = ['witness', 'status', 'description']
            datalist_fields = ['observer__observer_id', 'observer__name', 'location'] + data_fields

            export_fields = ['observer__observer_id', 'observer__name'] + location_type_fields + data_fields
            export_field_labels = ['PSZ', 'Name'] + location_types + ['Witness', 'Status', 'Description']

            datalist = self.filter_set.qs.data(data_fields).values(*datalist_fields)
            filename = slugify('%s %s analysis locations %s' % (self.display_tag, self.form.name, datetime.now().strftime('%Y %m %d %H%M%S')))
            response = HttpResponse(export(datalist, fields=export_fields, labels=export_field_labels), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s.xls' % (filename,)

            return response
        else:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)


class SubmissionListView(ListView):
    context_object_name = 'submissions'
    template_name = 'core/submission_list.html'
    paginate_by = settings.PAGE_SIZE
    page_title = ''

    def get_queryset(self):
        self.page_title = self.form.name
        return self.filter_set.qs.order_by('-date', 'observer__observer_id', '-created')

    def get_context_data(self, **kwargs):
        context = super(SubmissionListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('core.view_submission', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    def dispatch(self, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.submission_filter = generate_submission_filter(self.form)
        return super(SubmissionListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # handle messaging requests
        if 'action' in self.request.POST and self.request.POST['action'] == 'send_message':
            # messaging
            if request.user.has_perm('core.message_observers'):
                initial_data = request.session.get('submission_filter_%d' % self.form.pk, None)
                self.filter_set = self.submission_filter(initial_data,
                    queryset=Submission.objects.filter(form=self.form).exclude(observer=None).select_related(),
                    request=request)
                send_bulk_message(self.filter_set.qs.all().values_list('observer__pk', flat=True), self.request.POST['message'])
                return HttpResponse('OK')
            else:
                return HttpResponseForbidden()
        else:
            self.filter_set = self.submission_filter(self.request.POST,
                queryset=Submission.objects.filter(form=self.form).exclude(observer=None).select_related(),
                request=request)
            request.session['submission_filter_%d' % self.form.pk] = self.filter_set.form.data
            return super(SubmissionListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('submission_filter_%d' % self.form.pk, None)
        self.filter_set = self.submission_filter(initial_data,
            queryset=Submission.objects.filter(form=self.form).exclude(observer=None).select_related(),
            request=request)
        return super(SubmissionListView, self).get(request, *args, **kwargs)


class SubmissionEditView(UpdateView):
    template_name = 'core/submission_edit.html'
    page_title = 'Edit Submission'

    def get_object(self, queryset=None):
        return self.submission.master if self.submission.form.type == 'CHECKLIST' else self.submission

    @method_decorator(login_required)
    @method_decorator(permission_required('core.change_submission', return_403=True))
    def dispatch(self, *args, **kwargs):
        self.submission = get_object_or_404(Submission, pk=kwargs['pk'])
        self.form_class = generate_submission_form(self.submission.form)

        # submission_form_class allows for the rendering of form elements that are readonly
        # and disabled by default. It's only useful for rendering submission and submission
        # sibling records. Only the master submission should be editable.
        self.submission_form_class = generate_submission_form(self.submission.form, readonly=True)
        return super(SubmissionEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubmissionEditView, self).get_context_data(**kwargs)
        context['submission'] = self.submission

        # A prefix is defined to prevent a confusion with the naming
        # of the form field with other forms with the same field name
        context['submission_form'] = self.submission_form_class(instance=self.submission, prefix=self.submission.pk)

        # uses list comprehension to generate a list of forms that can be rendered to display
        # submission sibling form fields.
        context['submission_sibling_forms'] = [self.submission_form_class(instance=x, prefix=x.pk) for x in self.submission.siblings]
        context['location_types'] = LocationType.objects.filter(on_display=True)
        context['page_title'] = self.page_title
        return context

    def get_success_url(self):
        return reverse('submissions_list', args=[self.submission.form.pk])


class SubmissionCreateView(CreateView):
    template_name = 'core/submission_add.html'
    page_title = 'Add Submission'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.add_submission', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    def dispatch(self, *args, **kwargs):
        # we only want to allow creation of incident submissions
        self.form = get_object_or_404(Form, pk=kwargs['form'], type='INCIDENT')
        self.form_class = generate_submission_form(self.form)

        return super(SubmissionCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubmissionCreateView, self).get_context_data(**kwargs)
        context['form'] = self.form_class()
        context['form_pk'] = self.form.pk
        context['page_title'] = self.page_title
        return context

    def get_success_url(self):
        return reverse('submissions_list', args=[self.form.pk])


class SubmissionListExportView(View):
    collection = 'observers'

    # TODO: refactor to support custom field labels
    @method_decorator(login_required)
    @method_decorator(permission_required('core.export_submissions', return_403=True))
    def dispatch(self, request, *args, **kwargs):
        form = get_object_or_404(Form, pk=kwargs['form'])
        self.submission_filter = generate_submission_filter(form)
        initial_data = request.session.get('submission_filter_%d' % form.pk, None)
        if self.collection == 'master':
            self.filter_set = self.submission_filter(initial_data,
                queryset=Submission.objects.filter(form=form, observer=None), request=request)
        else:
            self.filter_set = self.submission_filter(initial_data,
                queryset=Submission.objects.filter(form=form).exclude(observer=None), request=request)
        qs = self.filter_set.qs.order_by('-date', 'observer__observer_id')

        location_types = list(LocationType.objects.filter(on_display=True).values_list('name', flat=True))
        location_type_fields = ['loc:location__{}'.format(lt.lower()) for lt in location_types]

        if form.type == 'CHECKLIST':
            data_fields = list(FormField.objects.filter(group__form=form).order_by('tag').values_list('tag', flat=True))
            datalist_fields = ['observer__observer_id', 'observer__name', 'observer__last_connection__identity', 'location', 'observer'] + data_fields + ['updated']

            if self.collection == 'master':
                export_fields = ['locobs:location__observer_id', 'locobs:location__name', 'locobs:location__phone', 'locobs:location__last_connection__identity'] + location_type_fields + data_fields + ['updated']
            else:
                export_fields = ['observer__observer_id', 'observer__name', 'obs:observer__phone', 'observer__last_connection__identity'] + location_type_fields + data_fields + ['updated']
            field_labels = ['PSZ', 'Name', 'Phone', 'Texted Phone'] + location_types + data_fields + ['Timestamp']

            datalist = qs.intdata(data_fields).values(*datalist_fields)
        else:
            data_fields = list(FormField.objects.filter(group__form=form).order_by('tag').values_list('tag', flat=True))

            export_fields = ['observer__observer_id', 'observer__name', 'obs:observer__phone', 'observer__last_connection__identity'] + location_type_fields + data_fields + ['status', 'witness', 'description', 'updated']
            field_labels = ['PSZ', 'Name', 'Phone', 'Texted Phone'] + location_types + data_fields + ['Status', 'Witness', 'Description', 'Timestamp']

            data_fields.extend(['status', 'witness', 'description'])
            datalist_fields = ['observer__observer_id', 'observer__name', 'location', 'observer', 'observer__last_connection__identity'] + data_fields + ['updated']

            datalist = qs.data(data_fields).values(*datalist_fields)

        filename = slugify('%s %s %s' % (form.name, datetime.now().strftime('%Y %m %d %H%M%S'), self.collection))
        response = HttpResponse(export(datalist, fields=export_fields, labels=field_labels), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.xls' % (filename,)

        return response


class VerificationListView(ListView):
    context_object_name = 'submissions'
    template_name = 'core/verification_list.html'
    paginate_by = settings.PAGE_SIZE
    page_title = 'Verification'

    def get_queryset(self):
        return self.filter_set.qs.order_by('-date', '-created')

    def get_context_data(self, **kwargs):
        context = super(VerificationListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('core.view_submission', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    def dispatch(self, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.submission_filter = generate_submission_flags_filter(self.form)
        return super(VerificationListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # force filtering to only occur on master CHECKLIST forms
        self.filter_set = self.submission_filter(self.request.POST,
            queryset=Submission.objects.filter(form=self.form, form__type='CHECKLIST', observer=None).select_related(),
            request=request)
        request.session['verification_filter_%d' % self.form.pk] = self.filter_set.form.data
        return super(VerificationListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('verification_filter_%d' % self.form.pk, None)
        self.filter_set = self.submission_filter(initial_data,
            queryset=Submission.objects.filter(form=self.form, form__type='CHECKLIST', observer=None).select_related(),
            request=request)
        return super(VerificationListView, self).get(request, *args, **kwargs)


class VerificationEditView(UpdateView):
    template_name = 'core/verification_edit.html'
    page_title = 'Edit Verification'

    def get_object(self, queryset=None):
        return self.submission

    @method_decorator(login_required)
    @method_decorator(permission_required('core.change_submission', return_403=True))
    def dispatch(self, *args, **kwargs):
        self.submission = get_object_or_404(Submission, pk=kwargs['pk'])
        self.form_class = generate_verification_form(self.submission.form)
        return super(VerificationEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(VerificationEditView, self).get_context_data(**kwargs)
        context['submission'] = self.submission
        context['flags'] = settings.FLAGS
        context['submission_form'] = self.form_class(instance=self.submission)
        context['location_types'] = LocationType.objects.filter(on_display=True)
        context['page_title'] = self.page_title
        return context

    def get_success_url(self):
        return reverse('verifications_list', args=[self.submission.form.pk])


class ContactListView(ListView):
    context_object_name = 'contacts'
    template_name = 'core/contact_list.html'
    model = Observer
    paginate_by = settings.PAGE_SIZE
    page_title = 'Observers'

    def get_queryset(self):
        return self.filter_set.qs.order_by('observer_id')

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        context['location_types'] = LocationType.objects.filter(on_display=True)
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('core.view_observers', return_403=True))
    def dispatch(self, *args, **kwargs):
        self.contacts_filter = generate_contacts_filter()
        return super(ContactListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # handle messaging requests
        if 'action' in self.request.POST and self.request.POST['action'] == 'send_message':
            # messaging
            if request.user.has_perm('core.message_observers'):
                initial_data = request.session.get('contacts_filter', None)
                self.filter_set = self.contacts_filter(initial_data,
                    queryset=Observer.objects.all())
                send_bulk_message(self.filter_set.qs.values_list('pk', flat=True), self.request.POST['message'])
                return HttpResponse('OK')
            else:
                return HttpResponseForbidden()
        else:
            self.filter_set = self.contacts_filter(request.POST,
                queryset=Observer.objects.all())
            request.session['contacts_filter'] = self.filter_set.form.data
            return super(ContactListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('contacts_filter', None)
        self.filter_set = self.contacts_filter(initial_data,
            queryset=Observer.objects.all())
        return super(ContactListView, self).get(request, *args, **kwargs)


class ContactEditView(UpdateView):
    template_name = 'core/contact_edit.html'
    model = Observer
    form_class = ContactModelForm
    success_url = '/observers/'
    page_title = 'Edit Observer'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.change_observer', return_403=True))
    def dispatch(self, *args, **kwargs):
        return super(ContactEditView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Observer, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(ContactEditView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class LocationListView(ListView):
    context_object_name = 'locations'
    template_name = 'core/location_list.html'
    model = Location
    paginate_by = settings.PAGE_SIZE
    page_title = 'Locations'

    def get_queryset(self):
        return self.filter_set.qs.order_by('pk')

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('core.view_locations', return_403=True))
    def dispatch(self, *args, **kwargs):
        self.locations_filter = LocationsFilter
        return super(LocationListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.filter_set = self.locations_filter(request.POST,
            queryset=Location.objects.all())
        request.session['locations_filter'] = self.filter_set.form.data
        return super(LocationListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('locations_filter', None)
        self.filter_set = self.locations_filter(initial_data,
            queryset=Location.objects.all())
        return super(LocationListView, self).get(request, *args, **kwargs)


class LocationEditView(UpdateView):
    template_name = 'core/location_edit.html'
    model = Location
    form_class = LocationModelForm
    success_url = '/locations/'
    page_title = 'Edit Location'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.change_location', return_403=True))
    def dispatch(self, *args, **kwargs):
        return super(LocationEditView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Location, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(LocationEditView, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class LocationShapeListView(ListView):
    context_object_name = 'locations'
    template_name = 'core/poly.kml'
    model = Location
    allowed_methods = ['GET']

    def get_queryset(self):
        return Location.objects.filter(type__name__iexact=self.type_name).select_related()

    def get_context_data(self, **kwargs):
        context = super(LocationShapeListView, self).get_context_data(**kwargs)
        return context

    def dispatch(self, *args, **kwargs):
        self.type_name = kwargs['type_name']
        return super(LocationShapeListView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super(LocationShapeListView, self).get(request, *args, **kwargs)


class CommentCreateView(View):
    http_method_names = ['post']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CommentCreateView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        submission = get_object_or_404(Submission, pk=request.POST['submission'])
        comment_text = request.POST['comment']

        if comment_text:
            comment = Comment.objects.create(content_object=submission,
                user_name=request.user.get_full_name() or request.user.username,
                user=request.user,
                site=Site.objects.get_current(), comment=comment_text, submit_date=datetime.now())
            response = {
                'comment': comment.comment,
                'date': 'now',
                'username': comment.user_name
            }
            return HttpResponse(json.dumps(response), mimetype='application/json')
        else:
            return HttpResponseBadRequest("")


def send_bulk_message(observers, message):
    observers = list(observers)  # cast to ValuesListQuery to list
    connections = []
    backend, _ = Backend.objects.get_or_create(name=settings.BULKSMS_BACKEND)
    for observer in Observer.objects.filter(pk__in=observers):
        if observer.phone:
            connection, _ = Connection.objects.get_or_create(
                identity=observer.phone, backend=backend, contact=observer.contact)
            connections.append(connection)
    # append numbers to be copied on every message
    for phone in settings.PHONE_CC:
        connection, _ = Connection.objects.get_or_create(
            identity=phone, backend=backend)
        connections.append(connection)
    if connections:
        send(message, connections)


def make_item_row(record, fields, locations_graph):
    row = []
    location_pattern = re.compile(r'^loc:(?P<field>\w+?)__(?P<location_type>\w+)$')  # pattern for location specification
    observer_pattern = re.compile(r'^obs:(?P<field>\w+?)__(?P<observer_field>.+)$')  # pattern for observer data
    # for master checklists, you cannot retrieve the observer because it's set to None the following attempts to
    # get this information from the location instead
    locationobserver_pattern = re.compile(r'^locobs:(?P<field>\w+?)__(?P<observer_field>\w+)$')

    for field in fields:
        location_match = location_pattern.match(field)
        observer_match = observer_pattern.match(field)
        locationobserver_match = locationobserver_pattern.match(field)

        if location_match:
            # if there's a match, retrieve the location name from the graph
            location_id = record[location_match.group('field')]
            location = get_location_ancestor_by_type(locations_graph, location_id, location_match.group('location_type'))
            row.append(location[0]['name'] if location else "")
        elif observer_match:
            # if there's an observer match, retrieve observer data from the field
            observer_id = record[observer_match.group('field')]
            try:
                observer = Observer.objects.get(pk=observer_id)
                row.append(r_getattr(observer, '.'.join(observer_match.group('observer_field').split('__'))))
            except Observer.DoesNotExist:
                row.append("")
        elif locationobserver_match:
            location_id = record[locationobserver_match.group('field')]
            try:
                observers = Location.objects.get(pk=location_id).observers.all()
                if observers:
                    observer = observers[0]
                    row.append(r_getattr(observer, '.'.join(locationobserver_match.group('observer_field').split('__'))))
                else:
                    row.append("")
            except Location.DoesNotExist:
                row.append("")
        else:
            if type(record[field]) == datetime or type(record[field]) == date:
                row.append(record[field].strftime('%Y-%m-%d %H:%M:%S'))
            else:
                row.append(record[field])

    return row


def export(datalist, fields, labels=[], **kwargs):
    '''Handles exporting a datalist to a (c)StringIO instance, with its
    contents being a spreadsheet in a specified format.

    `datalist` is the queryset to be exported with values already retrieved,
    the fields to be exported are specified as an array in the `fields` argument
    and there's an optional `labels` parameter for specifying column labels.

    location fields are specified as such:
        'loc:location__province'
    which enable the exporter to retrieve the location name in the progeny of
    the location of the specified location type.

    Also, a `format` keyword argument may be specified (defaulting to 'xls')
    that specifies the format to which the spreadsheet should be exported.
    Allowed values for the `format` argument are: 'ods', 'xls', 'xlsx', 'csv'
    '''
    locations_graph = get_locations_graph()
    dataset = tablib.Dataset()

    # grab keyword argument
    format = kwargs.pop('format', 'xls')
    format = 'xls' if format not in export_formats else format

    # set headers
    dataset.headers = labels or fields

    # retrieve data and build table
    for record in datalist:
        dataset.append(make_item_row(record, fields[:len(labels) if labels else len(fields)], locations_graph))

    return StringIO(getattr(dataset, format))


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect("{}?next={}".format(reverse('activity_selection'), redirect_to))
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)
