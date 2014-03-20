from ..core import Service
from .models import User


class UserService(Service):
    __model__ = User
