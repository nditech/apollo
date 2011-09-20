from webapp.api import *
from webapp.models import *
from models import *
from django.db.models import F, Q
from django.conf import settings

class ChecklistResponseResource(ModelResource):    
    class Meta:
        queryset = ZambiaChecklistResponse.objects.select_related()
        resource_name = 'checklist_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        ordering = ['monitor_name']


class ChecklistsResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True, null=True)
    response = fields.ToOneField(ChecklistResponseResource, 'response', full=True)

    class Meta:
        queryset = Checklist.objects.select_related('response', 'location__parent', 'location__parent__parent',
            'location__parent__parent__parent', 'location__parent__parent__parent__parent',
            'location__parent__parent__parent__parent__parent', 'location__parent__parent__parent__parent__parent__parent')
        resource_name = 'checklists'
        allowed_methods = ['get', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'response': ALL_WITH_RELATIONS,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer', 'response']

    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(ChecklistsResource, self).build_filters(filters)
        
        if orm_filters.has_key('location__id__exact') or orm_filters.has_key('location__id'):
            id = orm_filters.pop('location__id__exact')
            loc = Location.objects.get(id=id)
            if loc.type.name == 'Province':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'District':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Constituency':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Ward':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling District':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling Station':
                orm_filters['location__id__in'] = Location.objects.filter(parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling Stream':
                orm_filters['location__id__in'] = Location.objects.filter(id=id,type__name="Polling Stream").values_list('id', flat=True)
            
                
        if 'setup_status' in filters:
            status = filters.get('setup_status')
            if status == '1': # complete
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
                    'EB', 'EC', 'F', 'G', 'H', 'J']]))
                
            elif status == '2': # missing
                orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
                    'EB', 'EC', 'F', 'G', 'H', 'J']]))
                    
            elif status == '3': # partial
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
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)

        if 'voting_status' in filters:
            status = filters.get('voting_status')
            if status == '1': # complete
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']]))
                
            elif status == '2': # missing
                orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                    ['K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']]))
                    
            elif status == '3': # partial
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
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)

        if 'closing_status' in filters:
            status = filters.get('closing_status')
            if status == '1': # complete
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['X', 'Y', 'Z', 'AA']]))
                    
            elif status == '2': # missing
                orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                    ['X', 'Y', 'Z', 'AA']]))
                    
            elif status == '3': # partial
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
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)

        if 'counting_status' in filters:
            status = filters.get('counting_status')
            if status == '1': # complete
                if settings.ZAMBIA_DEPLOYMENT == 'RRP':
                    orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
                        'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
                        'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
                        'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))
                else:
                    orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
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
                    
            elif status == '2': # missing
                if settings.ZAMBIA_DEPLOYMENT == 'RRP':
                    orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                        ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
                        'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
                        'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
                        'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))
                else:
                    orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
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
                    
            elif status == '3': # partial
                query = None
                complete_query = None
                if settings.ZAMBIA_DEPLOYMENT == 'RRP':
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
                else:
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
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)
        
        if 'ecz_match' in filters:
            ecz_status = filters.get('ecz_match')
            if ecz_status == '1': # match
                query = Q(response__A__isnull=False)
                query |= Q(response__B__isnull=False)
                query |= Q(response__CA__isnull=False)
                query |= Q(response__CB__isnull=False)
                query |= Q(response__CC__isnull=False)
                query |= Q(response__CD__isnull=False)
                query |= Q(response__CE__isnull=False)
                query |= Q(response__CF__isnull=False)
                query |= Q(response__CG__isnull=False)
                query |= Q(response__CH__isnull=False)
                query |= Q(response__D__isnull=False)
                query |= Q(response__E__isnull=False)
                query |= Q(response__EA__isnull=False)
                query |= Q(response__EB__isnull=False)
                query |= Q(response__EC__isnull=False)
                query |= Q(response__F__isnull=False)
                query |= Q(response__G__isnull=False)
                query |= Q(response__H__isnull=False)
                
                pks = Checklist.objects.filter(query).filter(response__J=F('location__parent__code')).values_list('id', flat=True)
                
                if orm_filters.has_key('pk__in'):
                    orm_filters['pk__in'] = list(set(orm_filters['pk__in']) & set(pks))
                else:
                    orm_filters['pk__in'] = pks
                
            elif ecz_status == '2': # mismatch
                query = Q(response__A__isnull=False)
                query |= Q(response__B__isnull=False)
                query |= Q(response__CA__isnull=False)
                query |= Q(response__CB__isnull=False)
                query |= Q(response__CC__isnull=False)
                query |= Q(response__CD__isnull=False)
                query |= Q(response__CE__isnull=False)
                query |= Q(response__CF__isnull=False)
                query |= Q(response__CG__isnull=False)
                query |= Q(response__CH__isnull=False)
                query |= Q(response__D__isnull=False)
                query |= Q(response__E__isnull=False)
                query |= Q(response__EA__isnull=False)
                query |= Q(response__EB__isnull=False)
                query |= Q(response__EC__isnull=False)
                query |= Q(response__F__isnull=False)
                query |= Q(response__G__isnull=False)
                query |= Q(response__H__isnull=False)
                
                pks = Checklist.objects.filter(query).exclude(response__J=F('location__parent__code')).values_list('id', flat=True)
                
                if orm_filters.has_key('pk__in'):
                    orm_filters['pk__in'] = list(set(orm_filters['pk__in']) & set(pks))
                else:
                    orm_filters['pk__in'] = pks

        return orm_filters


class ChecklistResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True, null=True)
    form     = fields.ForeignKey(ChecklistFormResource, 'form')
    observer = fields.ForeignKey(ContactResource, 'observer', full=True, null=True, readonly=True)
    response = fields.ToOneField(ChecklistResponseResource, 'response', full=True, readonly=True)

    class Meta:
        queryset = Checklist.objects.select_related('response')
        resource_name = 'checklist'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class IncidentResponseResource(ModelResource):    
    class Meta:
        queryset = ZambiaIncidentResponse.objects.select_related()
        resource_name = 'incident_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        ordering = ['monitor_name']


class IncidentsResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True, null=True)
    response = fields.ToOneField(IncidentResponseResource, 'response', full=True)
    
    class Meta:
        queryset = Incident.objects.select_related()
        resource_name = 'incidents'
        allowed_methods = ['get', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
            'response': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer', 'response']

    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(IncidentsResource, self).build_filters(filters)
        
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            loc = Location.objects.get(id=id)
            if loc.type.name == 'Province':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'District':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Constituency':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Ward':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling District':
                orm_filters['location__id__in'] = Location.objects.filter(parent__parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling Station':
                orm_filters['location__id__in'] = Location.objects.filter(parent__id=id,type__name="Polling Stream").values_list('id', flat=True)
            elif loc.type.name == 'Polling Stream':
                orm_filters['location__id__in'] = Location.objects.filter(id=id,type__name="Polling Stream").values_list('id', flat=True)
        
        return orm_filters

class IncidentResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True, null=True)
    form     = fields.ForeignKey(IncidentFormResource, 'form')
    observer = fields.ForeignKey(ContactResource, 'observer', full=True, null=True)
    response = fields.ToOneField(IncidentResponseResource, 'response', full=True, readonly=True)
    
    class Meta:
        queryset = Incident.objects.select_related()
        resource_name = 'incident'
        allowed_methods = ['get', 'put', 'post']
        authentication = Authentication()
        authorization = Authorization()
