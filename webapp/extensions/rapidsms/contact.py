from webapp.models import ObserverRole, Location

class Observer(models.Model):
    """Election Observer"""
    observer_id = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    role = models.ForeignKey(ObserverRole)
    location = models.ForeignKey(Location)
    supervisor = models.ForeignKey('Contact')

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    class Meta:
        ordering = ['observer_id']

    def __unicode__(self):
        return self.name