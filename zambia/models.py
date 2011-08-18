from django.db import models
from webapp.models import ChecklistResponse, IncidentResponse
from django.core.validators import RegexValidator

# Create your models here.
class ZambiaChecklistResponse(ChecklistResponse):
    OPTIONS_A = (
        (1, 'Before 6am'),
        (2, 'At 6am'),
        (3, 'Between 6am and 7am'),
        (4, 'After 9am')
    )
    YES_NO = (
        (1, 'Yes'),
        (2, 'No')
    )
    OPTIONS_CB = (
        (1, '3 boxes present'),
        (2, '2 boxes present'),
        (3, '1 box present')
    )
    A = models.IntegerField(blank=True, null=True, choices=OPTIONS_A, validators=[RegexValidator(r'[1-4]')], help_text='At what time did people start voting at your polling stream? (if voting has not commenced by 9am complete a critical incident form)')
    B = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Was the polling stream set up so that voters could mark their ballot in secret? (if "No" complete a critical incident form)')
    CA = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Did the polling stream have Indelible Markers')
    CB = models.IntegerField(blank=True, null=True, choices=OPTIONS_CB, validators=[RegexValidator(r'[1-3]')], help_text='Did the polling stream have Three Ballot Boxes (Presidential, Parliamentary/National Assembly and Local Government)')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return str(self.checklist.id)

class ZambiaIncidentResponse(models.Model):
    A = models.NullBooleanField(blank=True)
    B = models.NullBooleanField(blank=True)
    C = models.NullBooleanField(blank=True)
    D = models.NullBooleanField(blank=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return str(self.incident.id)

