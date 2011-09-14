from django.db import models
from django.core.validators import RegexValidator
import re
from webapp.utility_models import ObserverRole, Location

class Observer(models.Model):
    """Election Observer"""
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    PARTNERS = (
        ('AVAP', 'AVAP'),
        ('Caritas', 'Caritas'),
        ('FODEP', 'FODEP'),
        ('OYV', 'OYV'),
        ('SACCORD', 'SACCORD'),
        ('TI-Z', 'TI-Z'),
        ('YWA', 'YWA'),
        ('ZNWL', 'ZNWL')
    )
    observer_id = models.CharField(max_length=100, validators=[RegexValidator(re.compile(r'\d+', re.I), message='Observer IDs can only contain numerals')])
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location)
    supervisor = models.ForeignKey('Contact', null=True, blank=True)
    gender = models.CharField(max_length=1, null=True, blank=True, choices=GENDER, db_index=True)
    partner = models.CharField(blank=True, null=True, max_length=100, choices=PARTNERS)
    nrc = models.CharField(blank=True, max_length=100, help_text='National Registration Card No.')
    cell_coverage = models.IntegerField(default=1, null=True, help_text='Does this contact have cell phone coverage?', db_index=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    class Meta:
        ordering = ['observer_id']

    def __unicode__(self):
        return self.name