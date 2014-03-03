from __future__ import unicode_literals
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import is_safe_url
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from core.documents import Event
from core.forms import EventSelectionForm


class EventSelectionView(View, TemplateResponseMixin):
    template_name = 'core/event_selection.html'

    def dispatch(self, request, *args, **kwargs):
        self.form_class = EventSelectionForm
        return super(
            EventSelectionView, self
        ).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'form': self.form}
        return context

    def get(self, request, *args, **kwargs):
        self.form = self.form_class(request=request)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = self.form_class(request.POST, request=request)
        if self.form.is_valid():
            request.session['event'] = Event.objects.with_id(
                self.form.cleaned_data['event']
            )

            redirect_to = request.REQUEST.get('next', '')
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_URL
                return HttpResponseRedirect(redirect_to)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class DashboardView(View, TemplateResponseMixin):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, world!')
