# -*- coding: utf-8 -*-
from collections import OrderedDict
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    import cPickle as pickle
except ImportError:
    import pickle
import re
from datetime import (date, datetime, timedelta)
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
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView, ListView, UpdateView, View, CreateView
from django.views.generic.base import TemplateResponseMixin
from djorm_expressions.base import SqlExpression, OR, AND
from jimmypage.cache import cache_page
from rapidsms.models import Connection, Backend
from guardian.decorators import permission_required
from guardian.shortcuts import get_objects_for_user
import tablib
import reversion
from apollo.core.forms import ActivitySelectionForm, ContactModelForm, LocationModelForm, generate_submission_form, generate_verification_form
from apollo.core.helpers import *
from apollo.core.messaging import send_bulk_message
from apollo.core.models import *
from apollo.core.filters import *
from apollo.core.utils import submission_diff
from analyses.datagenerator import generate_process_data, generate_incidents_data
from analyses.voting import incidents_csv

COMPLETION_STATUS = (
    (0, _('Complete')),
    (1, _('Partial')),
    (2, _('Empty')),
)

export_formats = ['csv', 'xls', 'xlsx', 'ods']


def set_activity(request, activity):
    request.session['activity'] = activity


def get_activity(request):
    return request.session.get('activity', Activity.default())


class TemplatePreview(TemplateView):
    page_title = ''

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplatePreview, self).get_context_data(**kwargs)
        context['page_title'] = self.page_title
        return context


class MapEmbedView(TemplateView):
    page_title = ''

    def dispatch(self, request, *args, **kwargs):
        self.template_name = 'core/map_embed.html'
        return super(TemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MapEmbedView, self).get_context_data(**kwargs)
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
            self.page_title = _('Dashboard') + u' · {}'.format(self.form_group.name)
            self.template_name = 'core/dashboard_status_breakdown.html'
        else:
            self.form_group = None
            self.page_title = _('Dashboard')
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


class IncidentsCSVView(View):
    def dispatch(self, request, *args, **kwargs):
        form = get_object_or_404(Form, pk=kwargs['form'], type="INCIDENT")
        lt = get_object_or_404(LocationType, pk=kwargs['locationtype'])
        if 'location' in kwargs:
            loc = get_object_or_404(Location, pk=kwargs['location'])
            qs = Submission.objects.filter(form=form).exclude(observer=None).is_within(loc)
        else:
            qs = Submission.objects.filter(form=form).exclude(observer=None)

        self.submission_filter = generate_submission_filter(form)
        self.filter_set = self.submission_filter(None,
            queryset=qs, request=request)
        df = self.filter_set.qs.dataframe()
        ds = tablib.Dataset()
        options = list(FormField.objects.filter(group__form=form).values_list('name', flat=True))
        ds.headers = ['LOC'] + options + ['TOT']
        for summary in incidents_csv(df, lt.name, options):
            ds.append([summary.get(heading) for heading in ds.headers])

        return HttpResponse(ds.csv, content_type='text/csv')


class SubmissionProcessAnalysisView(View, TemplateResponseMixin):
    template_name = 'core/checklist_summary.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_analyse', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    @method_decorator(cache_page)
    def dispatch(self, request, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.page_title = _('%(form)s Analysis') % {'form': self.form.name}
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
                self.tags = FormField.objects.filter(group__form=self.form, analysis_type='PROCESS').order_by('tag').values_list('tag', flat=True)
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
                self.page_title = _('%(form)s Analysis') % {'form': self.form.name}

        return super(SubmissionProcessAnalysisView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'params': kwargs}
        context['page_title'] = self.page_title
        context['filter_form'] = self.filter_set.form
        context['form'] = self.form
        context['location'] = self.location
        context['dataframe'] = self.filter_set.qs.dataframe()
        context['field_groups'] = OrderedDict()

        process_fields = FormField.objects.filter(analysis_type='PROCESS',
            group__form=self.form).order_by('group', 'tag')
        map(lambda field: context['field_groups'].setdefault(field.group.name, []).append(field), process_fields)

        context['display_tag'] = self.display_tag if hasattr(self, 'display_tag') else None
        if self.form.type == 'INCIDENT':
            if context['display_tag']:
                context['form_field'] = FormField.objects.get(group__form=self.form, tag=self.display_tag)
                context['location_types'] = LocationType.objects.filter(on_dashboard=True)
                context['incidents'] = self.filter_set.qs
                context['incidents_markers'] = get_incident_markers(self.form, self.filter_set.qs, 'Constituency', tag=True)
            else:
                context['incidents_summary'] = generate_incidents_data(self.form, self.filter_set.qs, self.location, grouped=self.grouped)
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
            export_field_labels = [ugettext('Observer ID'), ugettext('Name')] + location_types + [ugettext('Witness'), ugettext('Status'), ugettext('Description')]

            datalist = self.filter_set.qs.data(data_fields).values(*datalist_fields).distinct()
            filename = slugify('%s %s analysis locations %s' % (self.display_tag, self.form.name, datetime.now().strftime('%Y %m %d %H%M%S')))
            response = HttpResponse(export(datalist, fields=export_fields, labels=export_field_labels), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s.xls' % (filename,)

            return response
        else:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)


class SubmissionVotingResultsView(View, TemplateResponseMixin):
    template_name = 'core/results.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_analyse', return_403=True))
    @method_decorator(permission_required('core.view_form', (Form, 'pk', 'form'), return_403=True))
    @method_decorator(cache_page)
    def dispatch(self, request, *args, **kwargs):
        self.form = get_object_or_404(Form, pk=kwargs['form'])
        self.page_title = _('%(form)s Voting Results') % {'form': self.form.name}
        self.analysis_filter = generate_submission_analysis_filter(self.form)
        vote_options = []
        if 'location_id' in kwargs:
            self.location = get_object_or_404(Location, pk=kwargs['location_id'])
        else:
            self.location = Location.root()

        self.initial_qs = Submission.objects.filter(form=self.form, observer=None).where(~SqlExpression("data", "@>", "verification=>%s" % settings.FLAG_STATUSES['rejected'][0]))

        return super(SubmissionVotingResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'params': kwargs}
        context['page_title'] = self.page_title
        context['filter_form'] = self.filter_set.form
        context['form'] = self.form
        context['location'] = self.location
        context['dataframe'] = self.filter_set.qs.dataframe()

        return context

    def get(self, request, *args, **kwargs):
        self.filter_set = self.analysis_filter(request.GET, queryset=self.initial_qs, request=request)
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
    @method_decorator(permission_required('core.view_submissions', return_403=True))
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
    page_title = _('Edit Submission')

    def get_object(self, queryset=None):
        return self.master if self.submission.form.type == 'CHECKLIST' else self.submission

    @method_decorator(login_required)
    @method_decorator(permission_required('core.change_submission', return_403=True))
    def dispatch(self, *args, **kwargs):
        self.submission = get_object_or_404(Submission, pk=kwargs['pk'])
        self.form_class = generate_submission_form(self.submission.form)
        self.version = get_object_or_404(reversion.models.Version, pk=kwargs['version']) if kwargs.get('version', None) else None
        if self.version:
            self.submission = self.version.revision.version_set.get(object_id_int=self.submission.pk).object_version.object
            self.master = self.version.revision.version_set.get(object_id_int=self.submission.master.pk).object_version.object
        elif self.submission.form.type == 'CHECKLIST':
            self.master = self.submission.master


        # submission_form_class allows for the rendering of form elements that are readonly
        # and disabled by default. It's only useful for rendering submission and submission
        # sibling records. Only the master submission should be editable.
        self.submission_form_class = generate_submission_form(self.submission.form)
        return super(SubmissionEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SubmissionEditView, self).get_context_data(**kwargs)
        context['submission'] = self.submission
        
        context['versions'] = reversion.get_for_object(self.submission)
        context['submission_version'] = self.version

        if self.version:
            try:
                submission_old_version = reversion.get_for_date(self.submission, self.version.revision.date_created - timedelta(seconds=1))
                submission_old_version_object = submission_old_version.revision.version_set.get(object_id_int=self.submission.pk).object_version.object
                master_old_version_object = submission_old_version.revision.version_set.get(object_id_int=self.submission.master.pk).object_version.object
                context['submission_diff'] = submission_diff(submission_old_version_object, self.submission)
                context['master_diff'] = submission_diff(master_old_version_object, self.master)
            except Exception:
                context['submission_diff'] = submission_diff(Submission(), self.submission)
                context['master_diff'] = submission_diff(Submission(), self.master)

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()

        master_form = self.get_form(form_class)
        submission_form = self.submission_form_class(instance=self.submission, prefix=self.submission.pk, data=request.POST)

        if master_form.is_valid() and submission_form.is_valid():
            self.form_valid(master_form)
            return self.form_valid(submission_form)
        else:
            return self.form_invalid(master_form)


class SubmissionCreateView(CreateView):
    template_name = 'core/submission_add.html'
    page_title = _('Add Submission')

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
            datalist_fields = ['observer__observer_id', 'observer__name', 'observer__last_connection__identity', 'location', 'observer__contact__connection__identity'] + data_fields + ['updated']

            if self.collection == 'master':
                datalist_fields += ['submissions__observer__observer_id', 'submissions__observer__name', 'submissions__observer__contact__connection__identity', 'submissions__observer__last_connection__identity']
                export_fields = ['submissions__observer__observer_id', 'submissions__observer__name', 'submissions__observer__contact__connection__identity', 'submissions__observer__last_connection__identity'] + location_type_fields + data_fields + ['updated']
            else:
                export_fields = ['observer__observer_id', 'observer__name', 'observer__contact__connection__identity', 'observer__last_connection__identity'] + location_type_fields + data_fields + ['updated']
            field_labels = [ugettext('Observer ID'), ugettext('Name'), ugettext('Phone'), ugettext('Texted Phone')] + location_types + data_fields + [ugettext('Timestamp')]

            datalist = qs.intdata(data_fields).values(*datalist_fields).distinct()
        else:
            data_fields = list(FormField.objects.filter(group__form=form).order_by('tag').values_list('tag', flat=True))

            export_fields = ['observer__observer_id', 'observer__name', 'observer__contact__connection__identity', 'observer__last_connection__identity'] + location_type_fields + data_fields + ['status', 'witness', 'description', 'updated']
            field_labels = [ugettext('Observer ID'), ugettext('Name'), ugettext('Phone'), ugettext('Texted Phone')] + location_types + data_fields + [ugettext('Status'), ugettext('Witness'), ugettext('Description'), ugettext('Timestamp')]

            data_fields.extend(['status', 'witness', 'description'])
            datalist_fields = ['observer__observer_id', 'observer__name', 'location', 'observer__contact__connection__identity', 'observer__last_connection__identity'] + data_fields + ['updated']

            datalist = qs.data(data_fields).values(*datalist_fields).distinct()

        filename = slugify('%s %s %s' % (form.name, datetime.now().strftime('%Y %m %d %H%M%S'), self.collection))
        response = HttpResponse(export(datalist, fields=export_fields, labels=field_labels), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s.xls' % (filename,)

        return response


class VerificationListView(ListView):
    context_object_name = 'submissions'
    template_name = 'core/verification_list.html'
    paginate_by = settings.PAGE_SIZE
    page_title = _('Verification')

    def get_queryset(self):
        return self.filter_set.qs.order_by('-date', '-created')

    def get_context_data(self, **kwargs):
        context = super(VerificationListView, self).get_context_data(**kwargs)
        context['form'] = self.form
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title + u' · {}'.format(self.form.name)
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('core.view_submissions', return_403=True))
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
    page_title = _('Edit Verification')

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
        context['data_form'] = generate_submission_form(self.submission.form, readonly=True)(instance=self.submission, prefix=self.submission.pk)
        context['flags'] = self.submission.form.get_verification_flags()
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
    page_title = _('Observers')

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
                    queryset=Observer.objects.all().distinct())
                send_bulk_message(self.filter_set.qs.values_list('pk', flat=True), self.request.POST['message'])
                return HttpResponse('OK')
            else:
                return HttpResponseForbidden()
        else:
            self.filter_set = self.contacts_filter(request.POST,
                queryset=Observer.objects.all().distinct())
            request.session['contacts_filter'] = self.filter_set.form.data
            return super(ContactListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('contacts_filter', None)
        self.filter_set = self.contacts_filter(initial_data,
            queryset=Observer.objects.all().distinct())

        if request.GET.get('export', None):
            location_types = list(LocationType.objects.filter(on_display=True).values_list('name', flat=True))
            location_type_fields = ['loc:location__{}'.format(lt.lower()) for lt in location_types]
            datalist_fields = ['observer_id', 'name', 'location', 'location__name', 'role__name', 'partner__name', 'contact__connection__identity']

            export_fields = ['observer_id'] + location_type_fields + ['location__name', 'name', 'role__name', 'contact__connection__identity', 'partner__name']
            export_field_labels = [ugettext('Observer ID')] + location_types + [ugettext('Location'), ugettext('Name'), ugettext('Role'), ugettext('Phone'), ugettext('Partner')]

            datalist = self.filter_set.qs.values(*datalist_fields).distinct()
            filename = slugify('contacts %s' % (datetime.now().strftime('%Y %m %d %H%M%S')))
            response = HttpResponse(export(datalist, fields=export_fields, labels=export_field_labels), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s.xls' % (filename,)

            return response
        else:
            return super(ContactListView, self).get(request, *args, **kwargs)


class ContactEditView(UpdateView):
    template_name = 'core/contact_edit.html'
    model = Observer
    form_class = ContactModelForm
    success_url = '/observers/'
    page_title = _('Edit Observer')

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
    page_title = _('Locations')

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
    page_title = _('Edit Location')

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
