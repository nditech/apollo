from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = "My shiny new management command."

    def handle(self, *args, **options):
        user_count = 0
        print "Creating users..."
        if len(args):
            fh = open(args[0])
            line = fh.readline()
            while line:
                username = line.strip()
                try:
                    User.objects.create_user(username, "", username)
                    user_count += 1
                except IntegrityError:
                    pass
                line = fh.readline()
            print "%d users created." % user_count
        else:
            print "syntax: create_users user_file.txt"
