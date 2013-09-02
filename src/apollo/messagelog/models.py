from django.db import models


MESSAGE_INCOMING = 1
MESSAGE_OUTGOING = 2

MESSAGE_DIRECTION = (
    (MESSAGE_INCOMING, 'Incoming'),
    (MESSAGE_OUTGOING, 'Outgoing')
)


class MessageLog(models.Model):
    mobile = models.CharField(max_length=16, db_index=True)
    text = models.TextField(db_index=True)
    direction = models.SmallIntegerField(choices=MESSAGE_DIRECTION, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    delivered = models.DateTimeField(blank=True, null=True, db_index=True)

    def __unicode__(self):
        if self.direction == MESSAGE_INCOMING:
            return u'(IN) %s' % (self.mobile,)
        else:
            return u'(OUT) %s' % (self.mobile,)

    class Meta:
        permissions = (
            ("view_messages", "Can view the message log"),
            ("export_messages", "Can export the message log"),
        )
