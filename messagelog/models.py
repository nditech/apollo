from django.db import models


MESSAGE_INCOMING = 1
MESSAGE_OUTGOING = 2

MESSAGE_DIRECTION = (
    (MESSAGE_INCOMING, 'Incoming'),
    (MESSAGE_OUTGOING, 'Outgoing')
)


class MessageLog(models.Model):
    sender = models.CharField(max_length=16)
    text = models.TextField()
    direction = models.SmallIntegerField(choices=MESSAGE_DIRECTION)
    created = models.DateTimeField(auto_now_add=True)
    delivered = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        if self.direction == MESSAGE_INCOMING:
            return u'(IN) %s' % (self.sender,)
        else:
            return u'(OUT) %s' % (self.sender,)
