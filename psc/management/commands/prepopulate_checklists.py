from django.core.management.base import BaseCommand
from psc.models import VRChecklist, Observer, LGA
from django.contrib.contenttypes.models import ContentType
from psc.forms import VR_DAYS

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        # prepopulate vr checklists for LGA supervisors
        reports_created = 0
        lga_supervisors = Observer.objects.filter(location_type=ContentType.objects.get_for_model(LGA))
        for ls in lga_supervisors:
            for day in VR_DAYS:
                if day[0]:
                    report_date = day[0]
                    # check if there's a report already created for the observer
                    try:
                        vr = VRChecklist.objects.get(date=report_date, observer=ls)
                    except VRChecklist.DoesNotExist:
                        vr = VRChecklist(date=report_date, observer=ls)
                        vr.save()
                        reports_created += 1

        print "%d Voter's Registration Checklists Prepopulated" % reports_created
