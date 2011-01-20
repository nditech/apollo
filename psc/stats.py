from django.db.models import Q
from django.db import models
from models import *

def vr_QA(q=Q()):
    vrs = VRChecklist.objects.filter(q).filter(A__isnull=False).values('A')
    n = len(vrs)
    options = {1: 0, 2: 0, 3: 0, 4: 0}
    for vr in vrs:
        options[vr['A']] += 1
    return {'n': n, 'options': options }

def vr_QB(q=Q()):
    vrs = VRChecklist.objects.filter(q).filter(B__gt=0).values('B')
    n = len(vrs)
    options = {1: 0, 2: 0}
    for vr in vrs:
        options[vr['B']] += 1
    return {'n': n, 'options': options }

def vr_QC(q=Q()):
    vrs = VRChecklist.objects.filter(q).filter(C__isnull=False).values('C')
    total = len(vrs)
    valid = 0
    options = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    for vr in vrs:
        if vr['C'] in range(0, 10):
            key = vr['C']
            if options.has_key(key+1):
                options[key+1] += 1
                valid += 1
            else:
                options[6] += 1
                valid += 1
        else:
            options[6] += 1

    return {'n': total, 'valid_n': valid, 'options': options}

def vr_QD(q=Q()):
    qs = Q(D1__isnull=False) | Q(D2__isnull=False) | Q(D3__isnull=False) | Q(D4__isnull=False)
    vrs = VRChecklist.objects.filter(q).filter(qs).values('D1','D2', 'D3', 'D4')
    n = len(vrs)
    options = {1: 0, 2: 0, 3: 0, 4: 0}
    for vr in vrs:
        if vr['D1']:
            options[1] += 1
        if vr['D2']:
            options[2] += 1
        if vr['D3']:
            options[3] += 1
        if vr['D4']:
            options[4] += 1
    return {'n': n, 'options': options }

def vr_QE(q=Q()):
    qs = Q(E1__isnull=False) | Q(E2__isnull=False) | Q(E3__isnull=False) | Q(E4__isnull=False) | Q(E5__isnull=False)
    vrs = VRChecklist.objects.filter(q).filter(qs).values('E1','E2', 'E3', 'E4', 'E5')
    n = len(vrs)
    options = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for vr in vrs:
        if vr['E1']:
            options[1] += 1
        if vr['E2']:
            options[2] += 1
        if vr['E3']:
            options[3] += 1
        if vr['E4']:
            options[4] += 1
        if vr['E5']:
            options[5] += 1
    return {'n': n, 'options': options }

def vr_QF(q=Q()):
    pass

def vr_QG(q=Q()):
    pass

def vr_QH(q=Q()):
    pass

def vr_QJ(q=Q()):
    pass

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

