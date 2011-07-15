from django.core.management.base import BaseCommand
from django.contrib.auth.management import create_permissions
from django.db.models import get_apps

class Command(BaseCommand):
    help = "Updates model permissions."

    def handle(self, *args, **options):
        for app in get_apps():
            create_permissions(app, None, 2)