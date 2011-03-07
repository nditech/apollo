from django.core.management.base import BaseCommand
from psc.models import VRChecklist, DCOChecklist, Observer, RegistrationCenter, EDAYChecklist
from django.contrib.contenttypes.models import ContentType
from psc.forms import VR_DAYS, DCO_DAYS, EDAY_DAYS

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        # prepopulate vr checklists for LGA supervisors
        vr_reports_created = dco_reports_created = eday_reports_created = 0
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
                    try:
                        dco = DCOChecklist.objects.get(date=report_date, observer=ls)
                    except DCOChecklist.DoesNotExist:
                        dco = DCOChecklist(date=report_date, observer=ls)
                        dco.location_type = ContentType.objects.get_for_model(location)
                        dco.location_id = location.pk
                        dco.save()
                        dco_reports_created += 1

            
        observers = Observer.objects.filter(role__iexact='OBS')
        for observer in observers:
            for day in EDAY_DAYS[:-3] + EDAY_DAYS[-2:]:# This is set to remove the date for the senatorial election.
                if day[0]:
                    report_date = day[0]
                    rc = observer.location
                    eday, created = EDAYChecklist.objects.get_or_create(date=report_date, observer=observer, location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                    if created:
                        eday_reports_created += 1

        
        lga_supervisors = Observer.objects.filter(role__iexact='LGA')
        for lga_supervisor in lga_supervisors:
            for day in EDAY_DAYS[:-2]: # omit the last two dates
                if day[0]:
                    report_date = day[0]
                    rc = lga_supervisor.location
                    eday, created = EDAYChecklist.objects.get_or_create(date=report_date, observer=lga_supervisor, location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                    if created:
                        eday_reports_created += 1
                        
        print "%d Voter's Registration Checklists Prepopulated" % vr_reports_created
        print "%d Display, Claims and Objection Checklists Prepopulated" % dco_reports_created
        print "%d Election Day Checklists Prepopulated" % eday_reports_created
