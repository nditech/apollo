# -*- coding: utf-8 -*-
from http import HTTPStatus

from flask import jsonify
from flask_babelex import gettext as _

from apollo.core import red


def process_expired_token(jwt_header, jwt_payload):
    response = jsonify({
        'status': _('error'),
        'message': _('Token has expired')
    })
    response.status_code = HTTPStatus.UNAUTHORIZED
    return response


def process_invalid_token(reason):
    response = jsonify({
        'status': _('error'),
        'message': _(reason)
    })
    response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    return response


def process_revoked_token(jwt_header, jwt_payload):
    response = jsonify({
        'status': _('error'),
        'message': _('Token has been revoked')
    })
    response.status_code = HTTPStatus.UNAUTHORIZED
    return response


def check_if_token_is_blocklisted(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    entry = red.get(jti)

    return entry is not None
