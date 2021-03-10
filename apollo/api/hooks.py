# -*- coding: utf-8 -*-
from http import HTTPStatus

from flask import jsonify
from flask_babelex import gettext as _

from apollo.core import red


def process_expired_token(jwt_header, jwt_payload):
    return jsonify({
        'status': _('error'),
        'message': _('Token has expired')
    }), HTTPStatus.UNAUTHORIZED


def process_invalid_token(reason):
    return jsonify({
        'status': _('error'),
        'message': _(reason)
    }), HTTPStatus.UNPROCESSABLE_ENTITY


def process_revoked_token(jwt_header, jwt_payload):
    return jsonify({
        'status': _('error'),
        'message': _('Token has been revoked')
    }), HTTPStatus.UNAUTHORIZED


def check_if_token_is_blocklisted(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    entry = red.get(jti)

    return entry is not None
