from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import ListView
import tablib
from .models import MESSAGE_DIRECTION, MessageLog
from .filters import MessageFilter

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
    def dispatch(self, *args, **kwargs):
        return super(MessageListView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.filter_set = MessageFilter(self.request.POST,
            queryset=MessageLog.objects.all())
        request.session['message_filter'] = self.filter_set.form.data
        return super(MessageListView, self).get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        initial_data = request.session.get('message_filter', None)
        self.filter_set = MessageFilter(initial_data,
            queryset=MessageLog.objects.all())
        return super(MessageListView, self).get(request, *args, **kwargs)


def export_message_log(request, format='xls'):
    # grab all MessageLog objects
    message_log = MessageLog.objects.all()

    # tablib supports JSON, XLS, XLSX, CSV, YAML OOB, so maybe only for
    # something like PDF will we need anything else
    # (CAVEAT: tablib has dependencies for JSON & YAML output)
    data = tablib.Dataset()
    for log in message_log:
        row = [log.sender, log.text, directions[log.direction],
            log.created, log.delivered]

        data.append(row)

    data.headers = ['Mobile', 'Text', 'Message direction', 'Created',
        'Delivered']

    # create the response
    format = format.lower()
    if not format in export_formats:
        format = 'xls'

    response = HttpResponse(getattr(data, format),
        content_type=export_formats[format])

    # force a download
    response['Content-Disposition'] = 'attachment; filename=messagelog.' + format

    return response
