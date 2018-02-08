# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.users.rmodels import User, UserUpload


class UserService(Service):
    __model__ = User


class UserUploadService(Service):
    __model__ = UserUpload
