from . import route, permissions
from ..services import messages
from ..messaging.forms import MessagesFilterForm
from flask import (
    Blueprint, render_template, request, current_app, Response, g)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from datetime import datetime
from mongoengine import Q
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

    filter_form = MessagesFilterForm(request.args, csrf_enabled=False)
    filter_form.validate()

    mobile = filter_form.data.get('mobile')
    text = filter_form.data.get('text')
    date = filter_form.data.get('date')

    if mobile:
        qs = qs.filter(
            Q(recipient__contains=mobile) | Q(sender__contains=mobile))

    if text:
        qs = qs.filter(text__icontains=text)

    if date:
        qs = qs.filter(
            received__gte=datetime(date.year, date.month, date.day),
            received__lte=datetime(
                date.year, date.month, date.day, 23, 59, 59))

    if request.args.get('export'):
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
            'filter_form': filter_form,
            'args': data,
            'pager': qs.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE'))
        }

        return render_template(template_name, **context)
