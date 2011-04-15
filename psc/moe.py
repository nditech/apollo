from __future__ import division
from numpy import *
from django.db.models import Q
from psc.models import EDAYChecklist

def checklist_data_generator(qs=Q()):
    cls = EDAYChecklist.objects.filter(qs)
    no_of_parties = len(cls[0].contesting)
    parties = ['EA', 'EB', 'EC', 'ED', 'EE', 'EF', 'EG', 'EH', 'EJ', 'EK', 'EM', 'EN', 'EP', 'EQ', \
    		   'ER', 'ES', 'ET', 'EU', 'EV', 'EW', 'EX', 'EY', 'EZ', 'FA', 'FB', 'FC', 'FD', 'FE', 'FF', 'FG']
    fields = ['DA', 'DC'] + parties[0:no_of_parties]
    counter = 0
    for cl in cls:
    	if not counter:
    		data = array([[getattr(cl, field) if getattr(cl, field) else 0 for field in fields]])
    	else:
    		data = append(data, array([[getattr(cl, field) if getattr(cl, field) else 0 for field in fields]]), axis=0)
    	counter += 1
    
    return data

def margin_of_error(data, N=120000):
    ''' This method computes the margin of error for the election results per party.
    It expects the array in data to be in a certain format
    1. The first column contains the number of registered voters in each of the polling stations
    2. The second column contains the number of voters that participated in the elections as reported
       by the observer
    3. The other columns will contain the votes per party in each of the polling stations
    '''
    rv_array = data[:,0]
    part = data[:,1]
    pv = data[:,2:data.shape[1]]

    n = pv.shape[0]
    f = n / N
    RV = sum(rv_array)
    m = [sum(row) for row in pv] # actual calculation
    msr = ceil(RV / n)
    msr2 = msr**2
    p = [sum(pv[:,i]) / sum(m) for i in range(0, pv.shape[1])]
    num = ((1-f)/(n*msr2))

    deviations = []
    sum_of_deviations = []
    deg_of_freedom = []
    standard_error = []
    moe95 = []
    moe99 = []
    for j in range(0, pv.shape[1]):
        deviations.append([(pv[i,j] - p[j] * m[i])**2 for i in range(0, pv.shape[0])])
        sum_of_deviations.append(sum(deviations[j]))
        deg_of_freedom.append(sum_of_deviations[j]/ (n-1))
        standard_error.append(sqrt(num*deg_of_freedom[j]))
        moe95.append(standard_error[j]*196)
        moe99.append(standard_error[j]*258)
    
    return {'moe95': moe95, 'moe99': moe99}