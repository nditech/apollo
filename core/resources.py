from djangorestframework.resources import ModelResource
from django.core.urlresolvers import reverse
from djangorestframework.reverse import reverse
from formbuilder.models import Form
from models import *


class LocationResource(ModelResource):
    model = Location


class LocationTypeResource(ModelResource):
    model = LocationType
    fields = ('name', 'code', 'parent', 'id',)

    def parent(self, instance):
        return reverse('locationtype',
            kwargs={'pk': instance.parent.pk},
            request=self.request) if instance.parent else None


class ObserverResource(ModelResource):
    model = Observer


class PartnerResource(ModelResource):
    model = Partner


class SubmissionResource(ModelResource):
    model = Submission


class FormResource(ModelResource):
    model = Form
