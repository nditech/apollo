# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.users.rmodels import User


class UserService(Service):
    __model__ = User
