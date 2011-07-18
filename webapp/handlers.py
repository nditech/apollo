from apollo.django_restapi.model_resource import Collection
from apollo.django_restapi.responder import JSONResponder
from apollo.django_restapi.receiver import JSONReceiver
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from models import *

contact_resource = Collection(
    permitted_methods = ['GET', 'POST', 'PUT', 'DELETE'],
    queryset = Contact.objects.all(),
    responder = JSONResponder(),
    receiver = JSONReceiver(),
)

message_resource = Collection(
    permitted_methods = ['GET',],
    queryset = Message.objects.all(),
    responder = JSONResponder(),
    receiver = JSONReceiver(),
)
























#class MessageLogHandler(BaseHandler):
#    """Handler for the Message model"""
#    allowed_methods = ('GET',)
#    model = Message
#    fields = ('id', 'direction', 'date', 'text',)
#    
#    def read(self, request, msg_id=None):
#        if msg_id:
#            return self.model.objects.get(pk=msg_id)
#        else:
#            return self.model.objects.all()