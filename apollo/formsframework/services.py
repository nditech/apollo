# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.formsframework.models import Form, FormSet


class FormService(Service):
    __model__ = Form


class FormSetService(Service):
    __model__ = FormSet
