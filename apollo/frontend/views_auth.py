# -*- coding: utf-8 -*-
from __future__ import absolute_import
from flask.ext.login import login_user
from apollo.frontend.helpers import get_deployment
from apollo.frontend import route
from apollo.models import Deployment
from apollo.services import users
from flask import (
    Blueprint, abort, request, current_app, redirect, url_for
)
from urlparse import urlparse
import requests

bp = Blueprint('auth', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/auth/persona/login', methods=['POST'])
def persona_login():
    if 'assertion' not in request.form:
        abort(400)

    url = urlparse(request.url)
    try:
        hostname = url.hostname if get_deployment(url.hostname) else \
            Deployment.objects().first().hostnames[0]
    except:
        hostname = "localhost"

    if url.port:
        port = url.port
    else:
        port = 443 if url.scheme == "https" else 80

    data = {'assertion': request.form['assertion'],
            'audience': '{scheme}://{hostname}:{port}'.format(
                scheme=url.scheme, hostname=hostname, port=port)}
    resp = requests.post('https://verifier.login.persona.org/verify',
                         data=data, verify=True)

    if resp.ok:
        verification_data = resp.json()
        if verification_data['status'] == 'okay':
            # log the user in
            user = users.get(email=verification_data['email'])
            if user:
                login_user(user)
                return redirect(url_for('dashboard.index'))

    return current_app.login_manager.unauthorized()
