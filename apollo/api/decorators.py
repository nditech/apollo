# -*- coding: utf-8 -*-
from http import HTTPStatus

import wrapt
from flask import abort, current_app, jsonify, request
from flask_jwt_extended import verify_jwt_in_request
from flask_security import current_user


@wrapt.decorator
def protect(wrapped, instance, args, kwargs):
    # first, check if we have a user logged in
    if current_user and current_user.is_authenticated:
        return wrapped(*args, **kwargs)

    # if not, check if the API key was sent, and verify
    # if it is correct. send an unauthorized response
    # if it is not
    api_key = current_app.config.get('API_KEY', None)
    request_api_key = request.args.get('api_key', None)

    if request_api_key:
        if api_key == request_api_key:
            return wrapped(*args, **kwargs)
        response = jsonify({
            'status': 'error',
            'message': 'Access denied'
        })
        response.status_code = HTTPStatus.UNAUTHORIZED
        abort(response)

    # finally, assume that a JWT was sent
    verify_jwt_in_request()
    return wrapped(*args, **kwargs)
