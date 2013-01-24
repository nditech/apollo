from django.core.management.base import BaseCommand
from datetime import date
from webapp.models import *

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        print "Prepopulating checklists..."
        monitors = Contact.objects.filter(role__name="Monitor")
        checklist_form = ChecklistForm.objects.get(pk=1)
        
        checklist_count = 0
        for monitor in monitors:
            checklist, created = Checklist.objects.get_or_create(form=checklist_form, location=monitor.location, observer=monitor, date=date(2011, 9, 20))
            if created:
                checklist_count += 1
        
        print "%d Checklists prepopulated" % checklist_count
