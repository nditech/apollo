from django.db import models
from django_orm.postgresql import hstore
from formbuilder.models import Form
from .observer import Observer
from datetime import datetime


'''
The Observer model has evolved into becoming an extension for
the RapidSMS contact model. Details are in extensions/rapidsms/contact.py
'''


class Submission(models.Model):
    form = models.ForeignKey(Form, related_name='submissions')
    observer = models.ForeignKey(Observer, blank=True, null=True)
    date = models.DateField(default=datetime.today())
    data = hstore.DictionaryField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = hstore.HStoreManager()

    def __unicode__(self):
        return u"%s -> %s" % (self.pk, self.location,)
