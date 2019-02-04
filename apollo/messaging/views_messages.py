# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, timedelta

from dateutil.parser import parse
from dateutil.tz import gettz
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

from apollo.frontend import route, permissions
from apollo.messaging.filters import MessageFilterForm, MessageFilterSet
from apollo.models import Event, Form, Message, Submission
from apollo.services import events, messages
from apollo.settings import TIMEZONE


APP_TZ = gettz(TIMEZONE)
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
    )

    if request.args.get('export') and permissions.export_messages.can():
        # Export requested
        queryset_filter = MessageFilterSet(qs, request.args)
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
        filter_form = MessageFilterForm(request.args)
        filter_form.validate()
        filter_errors = filter_form.errors
        filter_data = filter_form.data
        OutboundMsg = aliased(Message, name='outbound')

        split_messages = qs.filter(
            sa.or_(
                Message.direction == 'IN',
                sa.and_(
                    Message.originating_message_id == None, # noqa
                    Message.direction == 'OUT'
                )
            )
        ).outerjoin(
            Submission, Message.submission_id == Submission.id
        ).outerjoin(
            Form, Submission.form_id == Form.id
        ).join(
            # TODO: add extra condition for 'OUT' message
            # if necessary
            OutboundMsg,
            sa.and_(
                OutboundMsg.originating_message_id == Message.id,
                OutboundMsg.direction == 'OUT',
            )
        )

        # filtering
        all_messages = split_messages.with_entities(
            Message, OutboundMsg, Submission.id, Form.form_type
        ).order_by(Message.received.desc())

        if 'mobile' not in filter_errors and filter_data.get('mobile'):
            val = f"%{filter_data.get('mobile')}%"
            all_messages = all_messages.filter(
                sa.or_(
                    Message.recipient.ilike(val),
                    Message.sender.ilike(val),
                    OutboundMsg.recipient.ilike(val)
                )
            )

        if 'text' not in filter_errors and filter_data.get('text'):
            val = f"%{filter_data.get('text')}%"
            all_messages = all_messages.filter(
                sa.or_(
                    Message.text.ilike(val),
                    OutboundMsg.text.ilike(val),
                )
            )

        if 'date' not in filter_errors and filter_data.get('date'):
            try:
                dt = parse(filter_data.get('date'), dayfirst=True)

                dt = dt.replace(
                    tzinfo=APP_TZ)

                date_end = dt.replace(hour=23, minute=59, second=59)
                date_start = dt.replace(hour=0, minute=0, second=0)

                all_messages = all_messages.filter(
                    sa.or_(
                        sa.and_(
                            Message.received >= date_start,
                            Message.received <= date_end
                        ),
                        sa.and_(
                            OutboundMsg.received >= date_start,
                            OutboundMsg.received <= date_end
                        ),
                    )
                )

            except (OverflowError, ValueError):
                all_messages = all_messages.filter(False)

        if 'form_type' not in filter_errors and (
                            filter_data.get('form_type') != ''):
            if filter_data.get('form_type') == 'Invalid':
                all_messages = all_messages.filter(
                    Message.submission_id == None   # noqa
                )
            else:
                all_messages = all_messages.filter(
                    Form.form_type == filter_data.get('form_type')
                )

        data = request.args.to_dict(flat=False)
        page_spec = data.pop('page', None) or [1]
        page = int(page_spec[0])
        context = {
            'page_title': page_title,
            'filter_form': filter_form,
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
