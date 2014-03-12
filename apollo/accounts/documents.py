from core.documents import Deployment
from mongoengine import ListField, ReferenceField
from mongoengine.django.auth import User as BaseUser


class User(BaseUser):
    deployments = ListField(ReferenceField(Deployment))
