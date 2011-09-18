// Backbone.js models

Screen = Backbone.Model.extend({
	defaults: {
		title: null,
		contents: null,
	},
	
	initialize: function () {
	    clearAllIntervals();
	}
});

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
    urlRoot: '/api/v1/incident/',
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
		reverserRelation: {
			key: 'incident'
		}
	}]
});
IncidentResponse = Backbone.RelationalModel.extend();

Checklist = Backbone.RelationalModel.extend({
    urlRoot: '/api/v1/checklist/',
	relations: [{
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: 'ChecklistForm',
		includeInJSON: 'resource_uri',
		reverseRelation: {
			key: 'checklists'
		}
	}, {
		type: Backbone.HasOne,
		key: 'location',
		relatedModel: 'Location',
		includeInJSON: 'resource_uri',
		reverseRelation: {
			key: 'checklists'
		} 
	}, {
		type: Backbone.HasOne,
		key: 'observer',
		relatedModel: 'Contact',
		includeInJSON: 'resource_uri',
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