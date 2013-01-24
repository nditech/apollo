from django.db.models import Q
from django.conf import settings

checklist_status = {
    'setup_complete': {},
    'setup_missing': {},
    'setup_partial': {},

    'voting_complete': {},
    'voting_missing': {},
    'voting_partial': {},

    'closing_complete': {},
    'closing_missing': {},
    'closing_partial': {},
    
    'counting_complete': {},
    'counting_missing': {},
    'counting_partial': {},
}

checklist_status['setup_complete'].update(dict([('response__%s__isnull' % field, False) for field in \
    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
    'EB', 'EC', 'F', 'G', 'H', 'J']]))
checklist_status['setup_missing'].update(dict([('response__%s__isnull' % field, True) for field in \
    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
    'EB', 'EC', 'F', 'G', 'H', 'J']]))
query = None
complete_query = None
for field in ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', \
    'E', 'EA', 'EB', 'EC', 'F', 'G', 'H', 'J']:
    if not query:
        exec 'query = Q(response__%s__isnull=False)' % field
    else:
        exec 'query |= Q(response__%s__isnull=False)' % field
    if not complete_query:
        exec 'complete_query = Q(response__%s__isnull=False)' % field
    else:
        exec 'complete_query &= Q(response__%s__isnull=False)' % field
exec 'query &= ~(complete_query)'
checklist_status['setup_partial'] = query


checklist_status['voting_complete'].update(dict([('response__%s__isnull' % field, False) for field in \
    ['K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']]))
checklist_status['voting_missing'].update(dict([('response__%s__isnull' % field, True) for field in \
    ['K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']]))
query = None
complete_query = None
for field in ['K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']:
    if not query:
        exec 'query = Q(response__%s__isnull=False)' % field
    else:
        exec 'query |= Q(response__%s__isnull=False)' % field
    if not complete_query:
        exec 'complete_query = Q(response__%s__isnull=False)' % field
    else:
        exec 'complete_query &= Q(response__%s__isnull=False)' % field
exec 'query &= ~(complete_query)'
checklist_status['voting_partial'] = query

checklist_status['closing_complete'].update(dict([('response__%s__isnull' % field, False) for field in \
    ['X', 'Y', 'Z', 'AA']]))
checklist_status['closing_missing'].update(dict([('response__%s__isnull' % field, True) for field in \
    ['X', 'Y', 'Z', 'AA']]))
query = None
complete_query = None
for field in ['X', 'Y', 'Z', 'AA']:
    if not query:
        exec 'query = Q(response__%s__isnull=False)' % field
    else:
        exec 'query |= Q(response__%s__isnull=False)' % field
    if not complete_query:
        exec 'complete_query = Q(response__%s__isnull=False)' % field
    else:
        exec 'complete_query &= Q(response__%s__isnull=False)' % field
exec 'query &= ~(complete_query)'
checklist_status['closing_partial'] = query

if settings.ZAMBIA_DEPLOYMENT == 'RRP':
    checklist_status['counting_complete'].update(dict([('response__%s__isnull' % field, False) for field in \
        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
        'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
        'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
        'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))

    checklist_status['counting_missing'].update(dict([('response__%s__isnull' % field, True) for field in \
        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
        'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
        'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
        'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))
        
    query = None
    complete_query = None
    for field in ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
    'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
    'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
    'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']:
        if not query:
            exec 'query = Q(response__%s__isnull=False)' % field
        else:
            exec 'query |= Q(response__%s__isnull=False)' % field
        if not complete_query:
            exec 'complete_query = Q(response__%s__isnull=False)' % field
        else:
            exec 'complete_query &= Q(response__%s__isnull=False)' % field
    exec 'query &= ~(complete_query)'
    checklist_status['counting_partial'] = query
else:
    checklist_status['counting_complete'].update(dict([('response__%s__isnull' % field, False) for field in \
        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEAC', 'AEAD', 'AEAE', 'AEAF', \
		'AEBA', 'AEBB', 'AEBC', 'AEBD', 'AEBE', 'AEBF', \
		'AECA', 'AECB', 'AECC', 'AECD', 'AECE', 'AECF', \
		'AEDA', 'AEDB', 'AEDC', 'AEDD', 'AEDE', 'AEDF', \
		'AEEA', 'AEEB', 'AEEC', 'AEED', 'AEEE', 'AEEF', \
		'AFAA', 'AFAB', 'AFAC', 'AFAD', 'AFAE', 'AFAF', \
		'AFBA', 'AFBB', 'AFBC', 'AFBD', 'AFBE', 'AFBF', \
		'AFCA', 'AFCB', 'AFCC', 'AFCD', 'AFCE', 'AFCF', \
		'AFDA', 'AFDB', 'AFDC', 'AFDD', 'AFDE', 'AFDF', \
		'AFEA', 'AFEB', 'AFEC', 'AFED', 'AFEE', 'AFEF', \
		'AFFA', 'AFFB', 'AFFC', 'AFFD', 'AFFE', 'AFFF', \
		'AFGA', 'AFGB', 'AFGC', 'AFGD', 'AFGE', 'AFGF', \
		'AFHA', 'AFHB', 'AFHC', 'AFHD', 'AFHE', 'AFHF', \
		'AFJA', 'AFJB', 'AFJC', 'AFJD', 'AFJE', 'AFJF', \
		'AFKA', 'AFKB', 'AFKC', 'AFKD', 'AFKE', 'AFKF', \
		'AFMA', 'AFMB', 'AFMC', 'AFMD', 'AFME', 'AFMF', \
		'AFNA', 'AFNB', 'AFNC', 'AFND', 'AFNE', 'AFNF', \
		'AFPA', 'AFPB', 'AFPC', 'AFPD', 'AFPE', 'AFPF', \
		'AFQA', 'AFQB', 'AFQC', 'AFQD', 'AFQE', 'AFQF', \
		'AG', 'AH', 'AJ', 'AK']]))
	
    checklist_status['counting_missing'].update(dict([('response__%s__isnull' % field, True) for field in \
        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEAC', 'AEAD', 'AEAE', 'AEAF', \
		'AEBA', 'AEBB', 'AEBC', 'AEBD', 'AEBE', 'AEBF', \
		'AECA', 'AECB', 'AECC', 'AECD', 'AECE', 'AECF', \
		'AEDA', 'AEDB', 'AEDC', 'AEDD', 'AEDE', 'AEDF', \
		'AEEA', 'AEEB', 'AEEC', 'AEED', 'AEEE', 'AEEF', \
		'AFAA', 'AFAB', 'AFAC', 'AFAD', 'AFAE', 'AFAF', \
		'AFBA', 'AFBB', 'AFBC', 'AFBD', 'AFBE', 'AFBF', \
		'AFCA', 'AFCB', 'AFCC', 'AFCD', 'AFCE', 'AFCF', \
		'AFDA', 'AFDB', 'AFDC', 'AFDD', 'AFDE', 'AFDF', \
		'AFEA', 'AFEB', 'AFEC', 'AFED', 'AFEE', 'AFEF', \
		'AFFA', 'AFFB', 'AFFC', 'AFFD', 'AFFE', 'AFFF', \
		'AFGA', 'AFGB', 'AFGC', 'AFGD', 'AFGE', 'AFGF', \
		'AFHA', 'AFHB', 'AFHC', 'AFHD', 'AFHE', 'AFHF', \
		'AFJA', 'AFJB', 'AFJC', 'AFJD', 'AFJE', 'AFJF', \
		'AFKA', 'AFKB', 'AFKC', 'AFKD', 'AFKE', 'AFKF', \
		'AFMA', 'AFMB', 'AFMC', 'AFMD', 'AFME', 'AFMF', \
		'AFNA', 'AFNB', 'AFNC', 'AFND', 'AFNE', 'AFNF', \
		'AFPA', 'AFPB', 'AFPC', 'AFPD', 'AFPE', 'AFPF', \
		'AFQA', 'AFQB', 'AFQC', 'AFQD', 'AFQE', 'AFQF', \
		'AG', 'AH', 'AJ', 'AK']]))

    query = None
    complete_query = None
    for field in ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEAC', 'AEAD', 'AEAE', 'AEAF', \
	'AEBA', 'AEBB', 'AEBC', 'AEBD', 'AEBE', 'AEBF', \
	'AECA', 'AECB', 'AECC', 'AECD', 'AECE', 'AECF', \
	'AEDA', 'AEDB', 'AEDC', 'AEDD', 'AEDE', 'AEDF', \
	'AEEA', 'AEEB', 'AEEC', 'AEED', 'AEEE', 'AEEF', \
	'AFAA', 'AFAB', 'AFAC', 'AFAD', 'AFAE', 'AFAF', \
	'AFBA', 'AFBB', 'AFBC', 'AFBD', 'AFBE', 'AFBF', \
	'AFCA', 'AFCB', 'AFCC', 'AFCD', 'AFCE', 'AFCF', \
	'AFDA', 'AFDB', 'AFDC', 'AFDD', 'AFDE', 'AFDF', \
	'AFEA', 'AFEB', 'AFEC', 'AFED', 'AFEE', 'AFEF', \
	'AFFA', 'AFFB', 'AFFC', 'AFFD', 'AFFE', 'AFFF', \
	'AFGA', 'AFGB', 'AFGC', 'AFGD', 'AFGE', 'AFGF', \
	'AFHA', 'AFHB', 'AFHC', 'AFHD', 'AFHE', 'AFHF', \
	'AFJA', 'AFJB', 'AFJC', 'AFJD', 'AFJE', 'AFJF', \
	'AFKA', 'AFKB', 'AFKC', 'AFKD', 'AFKE', 'AFKF', \
	'AFMA', 'AFMB', 'AFMC', 'AFMD', 'AFME', 'AFMF', \
	'AFNA', 'AFNB', 'AFNC', 'AFND', 'AFNE', 'AFNF', \
	'AFPA', 'AFPB', 'AFPC', 'AFPD', 'AFPE', 'AFPF', \
	'AFQA', 'AFQB', 'AFQC', 'AFQD', 'AFQE', 'AFQF', \
	'AG', 'AH', 'AJ', 'AK']:
        if not query:
            exec 'query = Q(response__%s__isnull=False)' % field
        else:
            exec 'query |= Q(response__%s__isnull=False)' % field
        if not complete_query:
            exec 'complete_query = Q(response__%s__isnull=False)' % field
        else:
            exec 'complete_query &= Q(response__%s__isnull=False)' % field
    exec 'query &= ~(complete_query)'
    checklist_status['counting_partial'] = query