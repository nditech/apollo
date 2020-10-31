# -*- coding: utf-8 -*-
import wrapt
from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request
from flask_security import current_user


@wrapt.decorator
def protect(wrapped, instance, args, kwargs):
    if current_user and current_user.is_authenticated:
        return wrapped(*args, **kwargs)

    api_key = current_app.config.get('API_KEY', None)
    request_api_key = request.args.get('api_key', None)

    if request_api_key and api_key == request_api_key:
        return wrapped(*args, **kwargs)

    verify_jwt_in_request()
    return wrapped(*args, **kwargs)
