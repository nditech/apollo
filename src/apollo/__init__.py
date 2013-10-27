import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apollo.settings')
from johnny.cache import enable
enable()
