from django.shortcuts import render


class EventSelectionView(View, TemplateResponseMixin):
    page_title = _('Select Event')
    template_name = 'core/event_selection.html'

    def dispatch(self, request, *args, **kwargs):
        self.form_class = EventSelectionForm
        return super(
            EventSelectionView, self
        ).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'form': self.form, 'page_title': self.page_title}
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
    page_title = 'Dashboard'
    template_name = 'core/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        event = request.session.get('event')
        if not event:
            return HttpResponseRedirect(reverse('event_selection'))
        forms = Form.objects(events=event, form_type='CHECKLIST')
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})
