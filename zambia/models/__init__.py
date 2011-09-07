from django.conf import settings

if getattr(settings, 'ZAMBIA_DEPLOYMENT', 'GENERAL') == 'GENERAL': # TODO: the default should be changed to RRP
    from general_models import *
else:
    from rrp_models import *