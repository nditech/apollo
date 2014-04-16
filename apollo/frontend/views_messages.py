from . import route, permissions
from ..services import messages
from ..messaging.forms import MessagesFilterForm
from flask import Blueprint, render_template, request, current_app
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from datetime import datetime
from mongoengine import Q


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
