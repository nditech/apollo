from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from guardian.decorators import permission_required
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import MESSAGE_DIRECTION, MessageLog
from .filters import MessageFilter
from core.views import export, get_activity

directions = dict(MESSAGE_DIRECTION)
export_formats = {'csv': 'text/csv', 'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet'}


class MessageListView(ListView):
    context_object_name = 'messages'
    template_name = 'messagelog/message_list.html'
    paginate_by = settings.PAGE_SIZE
    page_title = 'Messages'

    def get_queryset(self):
        return self.filter_set.qs.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(MessageListView, self).get_context_data(**kwargs)
        context['filter_form'] = self.filter_set.form
        context['page_title'] = self.page_title
        return context

    @method_decorator(login_required)
    @method_decorator(permission_required('messagelog.view_messages', return_403=True))
    def dispatch(self, *args, **kwargs):
        return super(MessageListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        activity = get_activity(request)
        self.filter_set = MessageFilter(self.request.POST,
            queryset=MessageLog.objects.filter(created__range=(activity.start_date, activity.end_date + timedelta(days=1))))
        request.session['message_filter'] = self.filter_set.form.data
        return super(MessageListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        activity = get_activity(request)
        initial_data = request.session.get('message_filter', None)
        self.filter_set = MessageFilter(initial_data,
            queryset=MessageLog.objects.filter(created__range=(activity.start_date, activity.end_date)))
        return super(MessageListView, self).get(request, *args, **kwargs)


def export_message_log(request, format='xls'):
    # grab all MessageLog objects
    message_log = MessageLog.objects.all()
    fields = ['mobile', 'text', 'direction', 'created', 'delivered']
    labels = ['Mobile', 'Text', 'Message direction', 'Created', 'Delivered']

    response = HttpResponse(export(message_log.values(*fields), fields=fields, labels=labels, format=format),
        content_type=export_formats[format])

    # force a download
    filename = slugify('messagelog %s' % (datetime.now().strftime('%Y %m %d %H%M%S'),))
    response['Content-Disposition'] = 'attachment; filename=%s.%s' % (filename, format)

    return response
