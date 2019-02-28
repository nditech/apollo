# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.formsframework.models import Form


class FormService(Service):
    __model__ = Form
