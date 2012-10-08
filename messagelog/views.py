from django.http import HttpResponse
import tablib
from .models import MESSAGE_DIRECTION, MessageLog

directions = dict(MESSAGE_DIRECTION)
export_formats = {'csv': 'text/csv', 'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet'}


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
