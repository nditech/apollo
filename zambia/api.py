from webapp.api import *
from webapp.models import *
from models import *
from django.db.models import Q

class ContactResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role')
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True)
    cell_coverage = fields.IntegerField('cell_coverage', null=True, blank=True)
    connections = fields.ToManyField(ConnectionResource, 'connection_set', readonly=True, full=True)
    
    class Meta:
        queryset = Contact.objects.select_related()
        resource_name = 'contact'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'connections': ALL_WITH_RELATIONS,
            'name': ('contains', 'icontains',),
            'observer_id': ('exact',),
            'location': ALL_WITH_RELATIONS,
            'partner': ('exact',),
            'cell_coverage': ('exact',),
        }


class ContactsResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role', full=True)
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True, full=True)
    cell_coverage = fields.IntegerField('cell_coverage', null=True, blank=True)
    connections = fields.ToManyField(ConnectionResource, 'connection_set', readonly=True, full=True)
    
    class Meta:
        queryset = Contact.objects.select_related()
        resource_name = 'contacts'
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'connections': ALL_WITH_RELATIONS,
            'name': ('contains', 'icontains',),
            'observer_id': ('exact',),
            'location': ALL_WITH_RELATIONS,
            'partner': ('exact',),
            'cell_coverage': ('exact',),
        }
        ordering = ['observer_id', 'name', 'role', 'location', 'connections', 'partner']
        
    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(ContactsResource, self).build_filters(filters)
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            orm_filters['location__id__in'] = Location.objects.get(id=id).get_descendants(True).values_list('id', flat=True)

        return orm_filters


class ChecklistResponseResource(ModelResource):    
    class Meta:
        queryset = ZambiaChecklistResponse.objects.select_related()
        resource_name = 'checklist_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class ChecklistsResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    response = fields.ToOneField(ChecklistResponseResource, 'response', full=True)

    class Meta:
        queryset = Checklist.objects.select_related()
        resource_name = 'checklists'
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'response': ALL_WITH_RELATIONS,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer']

    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(ChecklistsResource, self).build_filters(filters)
        
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            orm_filters['location__id__in'] = Location.objects.get(id=id).get_descendants(True).values_list('id', flat=True)
        
        # TODO: Filtering for general election checklists
        
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
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
                    'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
                    'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
                    'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))
                    
            elif status == '2': # missing
                orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                    ['AB', 'AC', 'AD', 'AEAA', 'AEAB', 'AEBA', 'AEBB', 'AECA', 'AECB', 'AEDA', \
                    'AEDB', 'AEEA', 'AEEB', 'AGA', 'AGB', 'AHA', 'AHB', 'AJA', 'AJB', 'AKA',  \
                    'AKB', 'AMA', 'AMB', 'ANA', 'ANB', 'APA', 'APB', 'AQA', 'AQB', 'ARA', \
                    'ARB', 'ASA', 'ASB', 'ATA', 'ATB', 'AUA', 'AUB', 'AV', 'AW', 'AX', 'AY']]))
                    
            elif status == '3': # partial
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
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)

        return orm_filters


class ChecklistResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True, null=True, readonly=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True, null=True, readonly=True)
    response = fields.ToOneField(ChecklistResponseResource, 'response', full=True)

    class Meta:
        queryset = Checklist.objects.select_related()
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


class IncidentsResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    response = fields.ToOneField(IncidentResponseResource, 'response', full=True)
    
    class Meta:
        queryset = Incident.objects.select_related()
        resource_name = 'incidents'
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
            'response': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer']

    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(IncidentsResource, self).build_filters(filters)
        
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            orm_filters['location__id__in'] = Location.objects.get(id=id).get_descendants(True).values_list('id', flat=True)
        
        print orm_filters
        return orm_filters

class IncidentResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location')
    observer = fields.ForeignKey(ContactResource, 'observer')
    response = fields.ToOneField(IncidentResponseResource, 'response', full=True)
    
    class Meta:
        queryset = Incident.objects.select_related()
        resource_name = 'incident'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
