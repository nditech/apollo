# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, timedelta

from flask import (
    Blueprint, Response, current_app, g, render_template, request,
    stream_with_context)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
import pandas as pd
from slugify import slugify_unicode
import sqlalchemy as sa
from sqlalchemy.orm import aliased

from apollo.frontend import filters, route, permissions
from apollo.models import Event, Form, Message, Submission
from apollo.services import events, messages


bp = Blueprint('messages', __name__)


@route(bp, '/messages', methods=['GET', 'POST'])
@register_menu(
    bp, 'main.messages',
    _('Messages'),
    icon='<i class="glyphicon glyphicon-envelope"></i>',
    visible_when=lambda: permissions.view_messages.can(),
    order=6)
@login_required
@permissions.view_messages.require(403)
def message_list():
    page_title = _('Messages')
    template_name = 'frontend/message_list.html'

    deployment = g.deployment
    message_events = set(events.overlapping_events(g.event)).union({g.event})
    event_ids = [ev.id for ev in message_events]
    qs = Message.query.filter(
        Message.deployment == deployment,
        Message.event_id.in_(event_ids)).order_by(
        Message.received.desc(), Message.direction.desc()
    ).outerjoin(
        Submission
    ).outerjoin(
        Form
    )
    queryset_filter = filters.messages_filterset()(qs, request.args)

    if request.args.get('export') and permissions.export_messages.can():
        # Export requested
        dataset = messages.export_list(queryset_filter.qs)
        basename = slugify_unicode('%s messages %s' % (
            g.event.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            stream_with_context(dataset),
            headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        Msg = aliased(Message)
        all_messages = queryset_filter.qs.filter(
            sa.or_(
                Message.direction == 'IN',
                sa.and_(
                    Message.originating_message_id == None, # noqa
                    Message.direction == 'OUT'
                )
            )
        ).join(
            # TODO: add extra condition for 'OUT' message
            # if necessary
            Msg, Msg.originating_message_id == Message.id
        ).with_entities(
            Message, Msg, Submission.id, Form.form_type
        ).order_by(Message.received.desc())

        data = request.args.to_dict(flat=False)
        page_spec = data.pop('page', None) or [1]
        page = int(page_spec[0])
        context = {
            'page_title': page_title,
            'filter_form': queryset_filter.form,
            'args': data,
            'pager': all_messages.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE')),
            'chart_data': message_time_series(all_messages)
        }

        return render_template(template_name, **context)


def message_time_series(message_queryset):
    c_events = events.overlapping_events(g.event).order_by(
        Event.start.desc())
    current_events = c_events.all() if c_events.count() > 0 else [g.event]

    # add 30 days as an arbitrary end buffer
    upper_bound = current_events[0].end + timedelta(30)
    lower_bound = current_events[-1].start

    # limit the range of the displayed chart to prevent possible
    # DOS attacks
    query = message_queryset.filter(
        Message.direction == 'IN',
        Message.received >= lower_bound,
        Message.received <= upper_bound
    ).with_entities(Message.received)

    df = pd.read_sql(query.statement, query.session.bind)

    # set a marker for each message
    df['marker'] = 1

    # set the index to the message timestamp, resample to hourly
    # and sum all markers in each hour, filling NaNs with 0
    if df.empty is not True:
        df = df.set_index('received').resample('1Min').sum().fillna(0)

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
