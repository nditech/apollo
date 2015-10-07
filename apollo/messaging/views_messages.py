from apollo.frontend import filters, route, permissions
from apollo.models import Message
from apollo.services import events, messages
from flask import (
    Blueprint, render_template, request, current_app, Response, g)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
import calendar
from datetime import datetime, timedelta
import pandas as pd
from slugify import slugify_unicode


bp = Blueprint('messages', __name__)


@route(bp, '/messages', methods=['GET', 'POST'])
@register_menu(
    bp, 'main.messages',
    _('Messages'),
    icon='<i class="glyphicon glyphicon-envelope"></i>',
    visible_when=lambda: permissions.view_messages.can(),
    order=6)
@permissions.view_messages.require(403)
def message_list():
    page_title = _('Messages')
    template_name = 'frontend/message_list.html'

    deployment = g.deployment
    qs = Message.objects(
        deployment=deployment,
        event__in=events.overlapping_events(g.event)).order_by(
        '-received', '-direction')
    queryset_filter = filters.messages_filterset()(qs, request.args)

    if request.args.get('export') and permissions.export_messages.can():
        # Export requested
        dataset = messages.export_list(queryset_filter.qs)
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
    current_events = list(events.overlapping_events(g.event).order_by(
        '-start_date'))
    # add 30 days as an arbitrary end buffer
    upper_bound = current_events[0].end_date + timedelta(30)
    lower_bound = current_events[-1].start_date

    # limit the range of the displayed chart to prevent possible
    # DOS attacks
    df = pd.DataFrame(
        list(message_queryset(
            direction='IN',
            received__gte=lower_bound,
            received__lte=upper_bound).only('received').as_pymongo()
        )
    )

    # set a marker for each message
    df['marker'] = 1

    # set the index to the message timestamp, resample to hourly
    # and sum all markers in each hour, filling NaNs with 0
    if df.empty is not True:
        df = df.set_index('received').resample('1Min', how='sum').fillna(0)

        # return as UNIX timestamp, value pairs
        data = {
            'incoming': [
                (calendar.timegm(i[0].utctimetuple()) * 1000, int(i[1]))
                for i in sorted(df.to_dict()['marker'].items())
            ]
        }
    else:
        data = {
            'incoming': []
        }

    return data
