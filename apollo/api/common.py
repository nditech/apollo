# -*- coding: utf-8 -*-
from flask.ext.restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument(u'limit', type=int)
parser.add_argument(u'offset', type=int)
