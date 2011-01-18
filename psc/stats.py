from django.db.models import Q
from django.db import models

def get_models_fields_exist(model, fields):
    if issubclass(model, models.Model):         
        def process_fields(fields):
            query = Q()
            for field in fields:
                if type(field) == 'list':
                    process_fields(field)
                else:
                    if issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField) and \
                        type(model._meta.get_field_by_name(field)[0].default) == int:
                        query &= eval('~Q(%s=%d)' % (field, model._meta.get_field_by_name(field)[0].default))
                    elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.IntegerField):
                        eval_str = '~Q(%s=0)' % field
                        query &= eval(eval_str)
                    elif issubclass(model._meta.get_field_by_name(field)[0].__class__, models.fields.BooleanField):
                        query &= eval('Q(%s=True)' % field)
                    else:
                        query &= eval('Q(%s__isnull=False)' % field)
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