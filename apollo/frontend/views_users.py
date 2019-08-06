# -*- coding: utf-8 -*-
from flask import Blueprint, redirect, render_template, url_for, abort
from flask_babelex import lazy_gettext as _
from flask_security import current_user, login_required
from flask_security.utils import encrypt_password

from apollo.frontend import route
from apollo.users import forms

bp = Blueprint('users', __name__)


@route(bp, '/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.has_role('field-coordinator'):
        abort(403)

    breadcrumbs = [_('Edit Profile')]
    user = current_user._get_current_object()
    form = forms.UserDetailsForm(instance=user)

    if form.validate_on_submit():
        data = form.data
        if data.get('password'):
            user.password = encrypt_password(data.get('password'))

        user.username = data.get('username')
        user.email = data.get('email')
        user.locale = data.get('locale') or None

        user.save()
        return redirect(url_for('dashboard.index'))

    context = {'form': form, 'breadcrumbs': breadcrumbs}

    return render_template('frontend/userprofile.html', **context)
