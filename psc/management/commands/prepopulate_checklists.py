from django.core.management.base import BaseCommand
from psc.models import VRChecklist, DCOChecklist, Observer, RegistrationCenter, EDAYChecklist
from django.contrib.contenttypes.models import ContentType
from psc.forms import VR_DAYS, DCO_DAYS, EDAY_DAYS

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        vr_reports_created = dco_reports_created = eday_reports_created = 0
        
        # prepopulate vr checklists for LGA supervisors
        if args[0] == 'vr':
            print "Prepopulating VR Checklists..."
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
            print "%d Voter's Registration Checklists Prepopulated" % vr_reports_created
            
        elif args[0] == 'dco':
            print "Prepopulating DCO Checklists..."
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
            print "%d Display, Claims and Objection Checklists Prepopulated" % dco_reports_created

        elif args[0] == 'eday':
            print "Prepopulating EDay Checklists..."
            observers = Observer.objects.filter(role__iexact='OBS')
            for observer in observers:
                for day in (EDAY_DAYS[1],) + EDAY_DAYS[-3:]:# This is set to remove the date for the senatorial election.
                    if day[0]:
                        report_date = day[0]
                        rc = observer.location
                        try:
                            eday = EDAYChecklist.objects.get(date=report_date, observer=observer, checklist_index='1' if int(observer.observer_id[-1]) % 2 else '2', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                        except EDAYChecklist.DoesNotExist:
                            eday = EDAYChecklist.objects.create(date=report_date, observer=observer, checklist_index='1' if int(observer.observer_id[-1]) % 2 else '2', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                            eday_reports_created += 1
                            
                    
                        if int(observer.observer_id[-1]) % 2:
                            try:
                                eday_control = EDAYChecklist.objects.get(date=report_date, observer=observer, checklist_index='3', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                            except EDAYChecklist.DoesNotExist:
                                eday_control = EDAYChecklist.objects.create(date=report_date, observer=observer, checklist_index='3', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                                eday_reports_created += 1
        
            lga_supervisors = Observer.objects.filter(role__iexact='LGA')
            for lga_supervisor in lga_supervisors:
                for day in EDAY_DAYS[1:3]: # omit the last two dates
                    if day[0]:
                        report_date = day[0]
                        rc = lga_supervisor.location
                        try:
                            eday = EDAYChecklist.objects.get(date=report_date, observer=lga_supervisor, checklist_index='1' if int(lga_supervisor.observer_id[-1]) % 6 else '2', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                        except EDAYChecklist.DoesNotExist:
                            eday = EDAYChecklist.objects.create(date=report_date, observer=lga_supervisor, checklist_index='1' if int(lga_supervisor.observer_id[-1]) % 6 else '2', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                            eday_reports_created += 1
                    
                    
                        if int(lga_supervisor.observer_id[-1]) % 6:
                            try:
                                eday_control = EDAYChecklist.objects.get(date=report_date, observer=lga_supervisor, checklist_index='3', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                            except EDAYChecklist.DoesNotExist:
                                eday_control = EDAYChecklist.objects.create(date=report_date, observer=lga_supervisor, checklist_index='3', location_type=ContentType.objects.get_for_model(rc), location_id=rc.id)
                                eday_reports_created += 1
                                
            print "%d Election Day Checklists Prepopulated" % eday_reports_created
