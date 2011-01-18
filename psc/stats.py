from django.db.models import Q
from django.db import models

def get_models_fields_exists(model, fields):
    if issubclass(model, models.Model):         
        def process_fields(fields, cond='AND'):
            query = Q()
            for field in fields:
                if type(field) == list:
                    query &= process_fields(field, 'OR')
                else:
                    if cond == 'AND':
                        if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                            type(model._meta.get_field_by_name(field)[0].default) == int:
                            query &= eval('~Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField):
                            query &= eval('Q(%s__isnull=False)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                            query &= eval('Q(%s=True)' % field)
                        else:
                            query &= eval('Q(%s__isnull=False)' % field)
                    else:
                        if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                            type(model._meta.get_field_by_name(field)[0].default) == int:
                            query |= eval('~Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField):
                            query |= eval('Q(%s__isnull=False)' % field)
                        elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                            query |= eval('Q(%s=True)' % field)
                        else:
                            query |= eval('Q(%s__isnull=False)' % field)
            return query
        
        return model.objects.filter(process_fields(fields))

def get_models_fields_missing(model, fields):
    if issubclass(model, models.Model):
        def process_fields(fields):
            query = Q()
            for field in fields:
                if type(field) == 'list':
                    process_fields(field)
                else:
                    if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                        type(model._meta.get_field_by_name(field)[0].default) == int:
                        query &= eval('Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                    elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                        query &= eval('Q(%s=False)' % field)
                    else:
                        query &= eval('Q(%s__isnull=True)' % field)
            return query
        
        return model.objects.filter(process_fields(fields))
