# -*- coding: utf-8 -*-
from http import HTTPStatus

from flask import jsonify
from flask_babelex import gettext as _

from apollo.core import red


def process_expired_token(payload):
    return jsonify({
        'status': _('error'),
        'message': _('Token has expired')
    }), HTTPStatus.UNAUTHORIZED


def process_invalid_token(description):
    return jsonify({
        'status': _('error'),
        'message': _(description)
    }), HTTPStatus.UNPROCESSABLE_ENTITY


def process_revoked_token():
    return jsonify({
        'status': _('error'),
        'message': _('Token has been revoked')
    }), HTTPStatus.UNAUTHORIZED


def check_if_token_is_blacklisted(decoded_token):
    jti = decoded_token['jti']
    entry = red.get(jti)

    if entry is None:
        return True

    return entry == b'true'
