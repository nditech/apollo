from celery.task import Task
from celery.registry import tasks
from urllib import quote_plus, urlencode
import urllib2
import xlrd
from xlwt import *
from models import *
from rapidsms.models import Backend
from django.conf import settings
        
class MessageBlast(Task):
    endpoint_sendsms = 'http://nusms.nuobjects.com/index.php'
    user = settings.SMS_USER
    pwd  = settings.SMS_PASS
    sender = settings.SMS_SENDER
    def run(self, to, msg):
        result = urllib2.urlopen(self.endpoint_sendsms, urlencode({
            'user': self.user,
            'pass': self.pwd,
            'from': self.sender,
            'to': to,
            'msg': msg})).read()
        if 'sent':
            return True
        else:
            return False
        

class ImportContacts(Task):
    def run(self, file_name):
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
                contact.connection_set.get_or_create(identity=row_vals[2],backend=Backend.objects.get(name="message_tester"))
            except Contact.DoesNotExist:
                new_contact = Contact.objects.create(observer_id=row_vals[0], name=row_vals[1], role=ObserverRole.objects.get(name=row_vals[3]), location = Location.objects.get(name=row_vals[4]))
                new_contact.connection_set.get_or_create(identity=row_vals[2],backend=Backend.objects.get(name="message_tester"))
        return True


class ExportContacts(Task):
    def run(self):
        wb = Workbook()
        ws = wb.add_sheet('0')
        contacts = Contact.objects.all()
        header = ["Observer_id","Name","Role","Location"]
        row = 0
        for i,j in enumerate(header):
            ws.write(row,i,"%s" % (j))
        #wb.save('C:\Users\owner\Desktop\excel\exp.xls')
        row = 1
        for contact in contacts:
            ws.write(row, 0, contact.observer_id)
            ws.write(row, 1, contact.name)
            ws.write(row, 2, contact.role.name)
            ws.write(row, 3, contact.location.name)
            row += 1
        wb.save('C:\Users\owner\Desktop\excel\exp.xls')



tasks.register(MessageBlast)
tasks.register(ImportContacts)
tasks.register(ExportContacts)