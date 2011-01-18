from django.db.models import Q
from django.db import models

def model_sieve(model, fields, exclude=False):
    if issubclass(model, models.Model):         
        def process_fields(fields, cond='AND'):
            query = Q()
            for field in fields:
                if type(field) == list:
                    query &= process_fields(field, 'OR')
                else:
                    if cond == 'AND':
                        if type(field) == tuple:
                            query &= eval('Q(%s=%s)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                            type(model._meta.get_field_by_name(field)[0].default) == int:
                            query &= eval('~Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField):
                            query &= eval('Q(%s__isnull=False)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                            query &= eval('Q(%s=True)' % field)
                        else:
                            query &= eval('Q(%s__isnull=False)' % field)
                    else:
                        if type(field) == tuple:
                            query &= eval('Q(%s=%s)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                            type(model._meta.get_field_by_name(field)[0].default) == int:
                            query |= eval('~Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField):
                            query |= eval('Q(%s__isnull=False)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                            query |= eval('Q(%s=True)' % field)
                        else:
                            query |= eval('Q(%s__isnull=False)' % field)
            return query
        
        if exclude:
            return model.objects.exclude(process_fields(fields))
        else:
            return model.objects.filter(process_fields(fields))

