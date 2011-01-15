from django.core.management.base import BaseCommand
from psc.models import VRChecklist, DCOChecklist, Observer, RegistrationCenter
from django.contrib.contenttypes.models import ContentType
from psc.forms import VR_DAYS, DCO_DAYS

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        # prepopulate vr checklists for LGA supervisors
        vr_reports_created = dco_reports_created = 0
        lga_supervisors = Observer.objects.filter(role__iexact='LGA')
        for ls in lga_supervisors:
            for day in VR_DAYS:
                if day[0]:
                    report_date = day[0]
                    # check if there's a report already created for the observer
                    lga = ls.location
                    # set default location
                    location = RegistrationCenter.objects.get(parent=lga,code__exact="999")
                    try:
                        vr = VRChecklist.objects.get(date=report_date, observer=ls)
                    except VRChecklist.DoesNotExist:
                        vr = VRChecklist(date=report_date, observer=ls)
                        vr.location_type = ContentType.objects.get_for_model(location)
                        vr.location_id = location.pk
                        vr.save()
                        vr_reports_created += 1

            for day in DCO_DAYS:
                if day[0]:
                    report_date = day[0]
                    # check if there's a report already created for the observer
                    lga = ls.location
                    # set default location
                    location = RegistrationCenter.objects.get(parent=lga,code__exact="999")
                    counter = 1
                    while counter <= 3:
                        try:
                            dco = DCOChecklist.objects.get(date=report_date, observer=ls, sms_serial=counter)
                        except DCOChecklist.DoesNotExist:
                            dco = DCOChecklist(date=report_date, observer=ls, sms_serial=counter)
                            dco.location_type = ContentType.objects.get_for_model(location)
                            dco.location_id = location.pk
                            dco.save()
                            dco_reports_created += 1
                        counter += 1

        print "%d Voter's Registration Checklists Prepopulated" % vr_reports_created
        print "%d Display, Claims and Objection Checklists Prepopulated" % dco_reports_created
