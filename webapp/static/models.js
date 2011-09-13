// Backbone.js models

Screen = Backbone.Model.extend({
	defaults: {
		title: null,
		contents: null,
	},
});

Backend = Backbone.RelationalModel.extend();
Location = Backbone.RelationalModel.extend({
    urlRoot: '/api/v1/location/',
    relations: [{
        type: Backbone.HasOne,
        key: 'parent',
        relatedModel: 'Location'
    }]
});
IncidentForm = Backbone.RelationalModel.extend();
ChecklistForm = Backbone.RelationalModel.extend();

Connection = Backbone.RelationalModel.extend({
    relations: [{
        type: Backbone.HasOne,
        key: 'backend',
        relatedModel: 'Backend',
        includeInJSON: 'resource_uri',
        reverseRelation: {
            key: 'connection'
        }
    }]
});

Message = Backbone.RelationalModel.extend({
    relations: [{
		type: Backbone.HasOne,
		key: 'connection',
		relatedModel: 'Connection',
		reverseRelation: {
			key: 'messages'
		}
	}, {
	    type: Backbone.HasOne,
	    key: 'contact',
	    relatedModel: 'Contact',
	    reverseRelation: {
	        key: 'messages'
	    }
	}]
});

Incident = Backbone.RelationalModel.extend({
	relations: [{
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: 'IncidentForm',
		includeInJSON: 'resource_uri',
		reverseRelation: {
			key: 'incidents'
		}
	},{
		type: Backbone.HasOne,
		key: 'location',
		relatedModel: 'Location',
		includeInJSON: 'resource_uri',
		reverseRelation: {
			key: 'incidents'
		}
	}, {
		type: Backbone.HasOne,
		key: 'observer',
		relatedModel: 'Contact',
		includeInJSON: 'resource_uri',
		reverseRelation: {
			key: 'incidents'
		}
	}, {
		type: Backbone.HasOne,
		key: 'response',
		relatedModel: 'IncidentResponse',
		includeInJSON: 'resource_uri',
		reverserRelation: {
			key: 'incident'
		}
	}]
});
IncidentResponse = Backbone.RelationalModel.extend();

Checklist = Backbone.RelationalModel.extend({
	relations: [{
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: 'ChecklistForm',
		reverseRelation: {
			key: 'checklists'
		}
	}, {
		type: Backbone.HasOne,
		key: 'location',
		relatedModel: 'Location',
		reverseRelation: {
			key: 'checklists'
		} 
	}, {
		type: Backbone.HasOne,
		key: 'observer',
		relatedModel: 'Contact',
		reverseRelation: {
			key: 'checklists'
		}	
	}, {
		type: Backbone.HasOne,
		key: 'response',
		relatedModel: 'ChecklistResponse',
		reverseRelation: {
			key: 'checklist'
		}
    }]
});
ChecklistResponse = Backbone.RelationalModel.extend();