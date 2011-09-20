from django.db.models import Q
from models import *
from numpy import *
import itertools

def checklist_N(q=Q()):
    n = Checklist.objects.filter(q).count()
    return n

def checklist_Q_options(question, q=Q()):
    exec 'checklists = [checklist.response.%s for checklist in list(Checklist.objects.select_related("response").filter(q).filter(response__%s__isnull=False))]' % (question, question) in globals(), locals()
    n = len(checklists)
    counts = dict((str(x), len(list(c))) for x, c in itertools.groupby(sorted(checklists)))
    return {'n': n, 'counts': counts }

def checklist_Q_mean(question, q=Q()):
    exec 'checklists = [checklist.response.%s for checklist in list(Checklist.objects.select_related("response").filter(q).filter(response__%s__isnull=False))]' % (question, question)
    n = len(checklists)
    m = mean(checklists) if n else 0
    return {'n': n, 'mean': m }