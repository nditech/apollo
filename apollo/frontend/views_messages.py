from . import filters, route, permissions
from ..services import messages
from flask import (
    Blueprint, render_template, request, current_app, Response, g)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
import calendar
from datetime import datetime
import pandas as pd
from slugify import slugify_unicode


bp = Blueprint('messages', __name__)


@route(bp, '/messages', methods=['GET', 'POST'])
@register_menu(
    bp, 'messages', _('Messages'),
    visible_when=lambda: permissions.view_messages.can())
@permissions.view_messages.require(403)
def message_list():
    page_title = _('Messages')
    template_name = 'frontend/message_list.html'

    qs = messages.all().order_by('-received')
    queryset_filter = filters.messages_filterset()(qs, request.args)

    if request.args.get('export') and permissions.export_messages.can():
        # Export requested
        dataset = messages.export_list(qs)
        basename = slugify_unicode('%s messages %s' % (
            g.event.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        data = request.args.to_dict()
        page = int(data.pop('page', 1))
        context = {
            'page_title': page_title,
            'filter_form': queryset_filter.form,
            'args': data,
            'pager': queryset_filter.qs.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE')),
            'chart_data': message_time_series(queryset_filter.qs)
        }

        return render_template(template_name, **context)


def message_time_series(message_queryset):
    subset = message_queryset(direction='IN')
    df = pd.DataFrame(list(subset.only('received').as_pymongo()))

    # set a marker for each message
    df['marker'] = 1

    # set the index to the message timestamp, resample to hourly
    # and sum all markers in each hour, filling NaNs with 0
    df = df.set_index('received').resample('1Min', how='sum').fillna(0)

    # do a cumulative sum of each row in the dataframe
    d = df.cumsum()

    # return as UNIX timestamp, value pairs
    data = [(calendar.timegm(i[0].utctimetuple()) * 1000, int(i[1]))
            for i in sorted(d.to_dict()['marker'].items())
            ]

    return data
