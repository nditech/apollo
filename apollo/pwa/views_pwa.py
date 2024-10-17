# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, jsonify, make_response, render_template, send_from_directory
from flask_babel import gettext as _

from apollo.frontend import route

blueprint = Blueprint("pwa", __name__, static_folder="static", template_folder="templates", url_prefix="/pwa")


@route(blueprint, "/")
def index():
    """Index view for the PWA."""
    commit = current_app.config["COMMIT"] or current_app.config["VERSION"]

    trace_errors = current_app.config["DEBUG"]
    sentry_dsn = current_app.config["SENTRY_DSN"] or ""

    context = {"commit": commit, "trace_errors": trace_errors}
    if trace_errors:
        context.update(dsn=sentry_dsn)
    page_title = _("Apollo")
    template_name = "pwa/index.html"

    context["page_title"] = page_title

    return render_template(template_name, **context)


@route(blueprint, "/serviceworker.js")
def service_worker():
    """Serve the service worker."""
    response = make_response(send_from_directory(blueprint.static_folder, path="js/serviceworker.js"))
    response.headers["Content-Type"] = "application/javascript"
    return response


@route(blueprint, "/versioncheck")
def version_check():
    """Version check endpoint for the PWA."""
    version = current_app.config["VERSION"]
    commit = current_app.config["COMMIT"] or version

    return jsonify({"version": version, "commit": commit})
