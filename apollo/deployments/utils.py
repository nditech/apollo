# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _

from apollo.deployments.models import Locale, deployment_locales


def get_deployment_locales(deployment_id):
    locales = Locale.query.join(
        deployment_locales
    ).filter(
        deployment_locales.c.deployment_id == deployment_id
    ).with_entities(
        Locale.code, Locale.name
    ).all()

    # return any locales found, or a default
    return locales or (('en', _('English')))
