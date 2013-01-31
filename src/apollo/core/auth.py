from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

analysts = Group(name='Analysts')
analysts.save()

data_clerks = Group(name='Data Clerks')
data_clerks.save()
