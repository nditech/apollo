# Create your views here.
from statistics import *
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, permission_required
from psc.forms import EDAYResultAnalysisFilterForm

@permission_required('psc.can_view_result', login_url='/')
@login_required()
def cumulative(request):
    date = '2011-04-16' # default date
    state_id = None
    
    if not request.session.has_key('eday_cum_chart_filter'):
        request.session['eday_cum_chart_filter'] = {}
    
    filter_form = EDAYResultAnalysisFilterForm(request.session['eday_cum_chart_filter'])

    if filter_form.is_valid():
        data = filter_form.cleaned_data

        if data['state']:
            state_id = data['state'] if data['state'] else None
        if data['date']:
            date = data['date'] if data['date'] else '2011-04-16'
                
    cumulative_data = cumulative_results_data_generator(date, state_id)
    datapoints = range(1, cumulative_data['data'].shape[0]+1)
    parties = cumulative_data['parties']
    colors = ['FD7ABD','0C3660','2A8643','DAD748','DB2A60','D108AA','5700AB','CDABE0','A5B19D','D67F2A',\
        '7F2355','676928','B9E80F','E0DE84','CBBBAF','FC5109','55E8C5','F5FC83','843B29','21E761','285DFB',\
        'F08FA4','AB0302','E5E7CD','373348','743C68','411901','DC694A','30102B','DF000A']
    party_data = {}
    for party_index in range(0, cumulative_data['data'].shape[1]-1):
        party_data[parties[party_index]] = ["%.2f" % float(i) for i in cumulative_data['data'][:,party_index]]
    
    return render_to_response('charts/convergence.xml', {'datapoints': datapoints, 'parties': parties, 'party_data': party_data, 'colors': colors }, mimetype='text/xml')