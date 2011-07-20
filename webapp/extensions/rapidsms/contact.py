from django.db import models
from django.core.validators import RegexValidator
import re
from webapp.utility_models import ObserverRole, Location

class Observer(models.Model):
    """Election Observer"""
    observer_id = models.CharField(max_length=100, validators=[RegexValidator(re.compile(r'\d+', re.I), message='Observer IDs can only contain numerals')])
    email = models.EmailField(blank=True)
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location)
    supervisor = models.ForeignKey('Contact', null=True, blank=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    class Meta:
        ordering = ['observer_id']

    def __unicode__(self):
        return self.name