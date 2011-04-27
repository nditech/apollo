from __future__ import division
from numpy import *
from psc.models import EDAYChecklist
from datetime import datetime

def cumulative_results_data_generator(date, state_id=None):
    party_codes = ['EA', 'EB', 'EC', 'ED', 'EE', 'EF', 'EG', 'EH', 'EJ', 'EK', 'EM', 'EN', 'EP', 'EQ', \
    		   'ER', 'ES', 'ET', 'EU', 'EV']
    party_names = ['ACN', 'ADC', 'ANPP', 'APS', 'ARP', 'BNPP', 'CPC', 'FRESH', 'HDP', 'MPPP', 'NCP', 'NMDP', 'NTP', 'PDC', 'PDP', 'PMP', 'PPP', 'SDMP', 'UNPD']
    if state_id:
        try:
            checklist = EDAYChecklist.objects.filter(date=datetime.strptime(date, '%Y-%m-%d').date(),observer__state__code=state_id)[0]
            party_codes = checklist.contesting
            party_names = [checklist.parties[i] for i in party_codes]
        except IndexError:
            pass
    
    # TODO: add condition for checking that at least on party has a vote (zero is allowed)
    if state_id:
        extra_fields = ", ".join(["SUM(eday.%s) AS sum_%s" % (code, code.upper()) for code in party_codes])
        query = "SELECT eday.*, " + extra_fields + " FROM psc_edaychecklist eday, psc_observer obs, psc_state state WHERE eday.date=%s AND eday.DA IS NOT NULL AND eday.DG IS NOT NULL AND eday.observer_id=obs.id AND obs.state_id=state.id AND state.code=%s GROUP BY HOUR(last_updated), MOD(MINUTE(last_updated), 4)"
        checklists = EDAYChecklist.objects.raw(query, [date, state_id])
    else:
        extra_fields = ", ".join(["SUM(%s) AS sum_%s" % (code, code.upper()) for code in party_codes])
        query = "SELECT *, " + extra_fields + " FROM psc_edaychecklist WHERE date=%s AND DA IS NOT NULL AND DG IS NOT NULL GROUP BY HOUR(last_updated), MOD(MINUTE(last_updated), 4)"
        checklists = EDAYChecklist.objects.raw(query, [date])
    
    # compute the cumulative figures
    counter = 0
    for cl in checklists:
        if not counter:
            data = array([[getattr(cl, 'sum_%s' % code.upper()) if getattr(cl, 'sum_%s' % code.upper()) else 0 for code in party_codes]])
        else:
            last_row = data[data.shape[0]-1,:]
            insert_row = array([getattr(cl, 'sum_%s' % code.upper()) if getattr(cl, 'sum_%s' % code.upper()) else 0 for code in party_codes])
            data = append(data, array([last_row + insert_row]), axis=0)
        counter += 1
    
    # compute the sums of the votes for each party
    summation = array([sum(data[row,:]) for row in range(0, data.shape[0])])
    
    # append the summation to the end of the columns
    data = append(data, summation.reshape(summation.shape[0], 1), axis=1)
    
    # calculate percentages
    for row in range(0, data.shape[0]):
        for column in range(0, data.shape[1]-1):
            data[row,column] = data[row,column] / data[row,data.shape[1]-1] * 100
    
    return {'data': data, 'parties': party_names }