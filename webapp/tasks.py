from celery.task import Task
from celery.registry import tasks
from urllib import quote_plus, urlencode
import urllib2
import xlrd, xlwt
from models import *
from django.conf import settings



class MyTask(Task):
    def run(self, x, y):
        return x + y

        
class MessageBlast(Task):
    endpoint_sendsms = 'http://api2.infobip.com/api/sendsms/plain?user=%(user)&password=%(pwd)&sender=%(sender)&SMSText=%(msg)&GSM=%(to)'
    user = settings.SMS_USER
    pwd  = settings.SMS_PASS
    sender = settings.SMS_PREFIX
    def run(self, to, msg):
        result = urllib2.urlopen(self.endpoint_sendsms, urlencode({
            'user': self.user,
            'pass': self.pwd,
            'from': self.sender,
            'to': to,
            'msg': msg})).read()
        if int(result.strip()) > 0:
            return True
        else:
            return False
        

class GetContact(Task):
    def run(self, file_name):
        try:
            choice_file = xlrd.open_workbook(file_name)
            choice_sheet = choice_file.sheet_by_index(0)
            for row_num in range(choice_sheet.nrows):
                row_vals = choice_sheet.row_values(row_num)
                try:
                    contact = Contact.objects.get(observer_id = row_vals[0])
                    contact.name = row_vals[1]
                    contact.role = ObserverRole.objects.get(name=row_vals[3])
                    contact.location = Location.objects.get(name=row_vals[4])
                    contact.save()
                except Contact.DoesNotExist:
                    new_contact = Contact.objects.create(observer_id=row_vals[0], name=row_vals[1], role=ObserverRole.objects.get(name=row_vals[3]), location = Location.objects.get(name=row_vals[4]))
        except:
            return True

tasks.register(MyTask)
tasks.register(MessageBlast)
tasks.register(GetContact)