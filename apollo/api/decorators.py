# -*- coding: utf-8 -*-
from functools import wraps

from flask import current_app, request
from flask_security import current_user


def login_or_api_key_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user and current_user.is_authenticated:
            return func(*args, **kwargs)

        api_key = current_app.config.get('API_KEY', None)
        request_api_key = request.args.get('api_key', None)

        if request_api_key and api_key == request_api_key:
            return func(*args, **kwargs)

        return current_app.login_manager.unauthorized()

    return decorated_view
