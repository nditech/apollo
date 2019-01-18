# -*- coding: utf-8 -*-
from flask import Blueprint, redirect, render_template, url_for
from flask_babelex import lazy_gettext as _
from flask_security import current_user, login_required
from flask_security.utils import encrypt_password

from apollo.frontend import route
from apollo.users import forms

bp = Blueprint('users', __name__)


@route(bp, '/users/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    page_title = _('Edit Profile')
    user = current_user._get_current_object()
    form_class = forms.user_details_form_factory(user)
    form = form_class()

    if form.validate_on_submit():
        data = form.data
        if data.get('password'):
            user.password = encrypt_password(data.get('password'))

        user.username = data.get('username')
        user.email = data.get('email')
        user.locale = data.get('locale')

        user.save()
        return redirect(url_for('dashboard.index'))

    context = {'form': form, 'page_title': page_title}

    return render_template('frontend/userprofile.html', **context)
