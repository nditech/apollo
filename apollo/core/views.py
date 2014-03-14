from __future__ import absolute_import
from __future__ import unicode_literals
from flask import Blueprint, current_app as app, flash, g, redirect, render_template, url_for
from flask.ext.babel import lazy_gettext as _
from core.forms import generate_event_selection_form, generate_location_edit_form
from core.models import Event, Location

core = Blueprint('core', __name__, template_folder='templates',
                 static_folder='static', static_url_path='/core/static')


@core.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@core.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@core.app_errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@core.route('/')
def index():
    return 'Hello, world!'


@core.route('/event', methods=['GET', 'POST'])
def event_selection():
    page_title = _('Select event')
    template_name = 'core/event_selection.html'

    if request.method == 'GET':
        form = generate_event_selection_form(g.deployment)
    elif request.method == 'POST':
        form = generate_event_selection_form(g.deployment, request.form)

        if form.validate():
            try:
                event = Event.objects.get(pk=form.event.data)
            except Event.DoesNotExist:
                flash(_('Selected event not found'))
                return render_template(template_name, form=form, page_title=page_title)

            g.event = event
            return redirect(url_for('core.index'))

    return render_template(template_name, form=form, page_title=page_title)


@core.route('/location/<pk>')
def location_edit(pk):
    location = Location.objects.get_or_404(pk=pk)
    if request.method == 'GET'
