from django.core.management.base import BaseCommand
from psc.models import Observer
from rapidsms.models import Contact

class Command(BaseCommand):
    help = "Creates the 'ghost' LGA observers."

    def handle(self, *args, **options):
        created_observers = 0
        lga_observers = Observer.objects.filter(role="LGA", position=1)
        for lga_observer in lga_observers:
            new_lga_observer, created = Observer.objects.get_or_create(observer_id="%d" % (int(lga_observer.observer_id)+5), \
                location_type=lga_observer.location_type, location_id=lga_observer.location_id, 
                supervisor=lga_observer.supervisor, partner=lga_observer.partner, role=lga_observer.role, 
                gender=lga_observer.gender, position=2)
            if created:
                created_observers += 1
                new_lga_observer.contact = Contact()
                new_lga_observer.contact.save()
                new_lga_observer.save()
        print "%d LGA ghost supervisors created." % created_observers