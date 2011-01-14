from django.db.models import Q
from django.db import models

def get_models_fields_exist(model, fields, optional_fields=[]):
    if issubclass(model, models.Model):
        query = Q()
        optional_query = Q(pk__isnull=False)

        for field in fields:
            if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                not issubclass(model._meta.get_field_by_name(field)[0].default, models.fields.NOT_PROVIDED):
                query &= eval('Q(%s__gte=0)' % field)
            elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                query &= eval('Q(%s=True)' % field)
            else:
                query &= eval('Q(%s__isnull=False)' % field)

        for field in optional_fields:
            if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                not issubclass(model._meta.get_field_by_name(field)[0].default, models.fields.NOT_PROVIDED):
                optional_query |= eval('Q(%s__gte=0)' % field)
            elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                query &= eval('Q(%s=True)' % field)
            else:
                optional_query |= eval('Q(%s__isnull=False)' % field)

        if optional_query:
            query &= (optional_query)

        return model.objects.filter(query)

def get_models_fields_missing(model, fields, optional_fields=[]):
    if issubclass(model, models.Model):
        query = Q()
        optional_query = Q(pk__isnull=False)

        for field in fields:
            if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                not issubclass(model._meta.get_field_by_name(field)[0].default, models.fields.NOT_PROVIDED):
                query &= eval('Q(%s=0)' % field)
            elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                query &= eval('Q(%s=False)' % field)
            else:
                query &= eval('Q(%s__isnull=True)' % field)

        for field in optional_fields:
            if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                not issubclass(model._meta.get_field_by_name(field)[0].default, models.fields.NOT_PROVIDED):
                optional_query |= eval('Q(%s=0)' % field)
            elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                query &= eval('Q(%s=False)' % field)
            else:
                optional_query |= eval('Q(%s__isnull=True)' % field)

        if optional_query:
            query &= (optional_query)

        return model.objects.filter(query)
