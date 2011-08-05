from celery.task import Task
from celery.registry import tasks
from urllib import quote_plus, urlencode
import urllib2
from django.conf import settings



class MyTask(Task):
    def run(self, x, y):
        return x + y


class SendMsg(Task):
    endpoint_sendsms = 'http://api.nodsms.com/index.php'
    endpoint_balance = 'http://api.nodsms.com/credit.php?user=%(user)s&pass=%(pass)s'
    user = "dipo"
    pwd  = "father7777"
    
    def run(self, to, msg, sender="HEMHEM"):
        result = urllib2.urlopen(self.endpoint_sendsms, urlencode({
            'user': self.user,
            'pass': self.pwd,
            'from': sender,
            'to': to,
            'msg': msg})).read()
        if result.strip() == 'sent':
            return True
        else:
            return False
        
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
        if result.strip() == 'sent':
            return True
        else:
            return False

tasks.register(MyTask)
tasks.register(SendMsg)
tasks.register(MessageBlast)



