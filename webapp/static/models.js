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
ChecklistQuestion = Backbone.RelationalModel.extend();
ChecklistQuestionType = Backbone.RelationalModel.extend();
ChecklistForm = Backbone.RelationalModel.extend();

Connection = Backbone.RelationalModel.extend({
    relations: [{
        type: Backbone.HasOne,
        key: 'backend',
        relatedModel: 'Backend',
        reverseRelation: {
            key: 'connections'
        }
    }]
});

Contact = Backbone.RelationalModel.extend({
    relations: [{
        type: Backbone.HasMany,
		key: 'connections',
		relatedModel: 'Connection',
		reverserRelation: {
			key: 'contacts'
		}
    },{
        type: Backbone.HasOne,
        key: 'supervisor',
        relatedModel: 'Contact'
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
		key: 'location',
		relatedModel: 'Location',
		reverseRelation: {
			key: 'incidents'
		}
	}, {
		type: Backbone.HasOne,
		key: 'observer',
		relatedModel: 'Contact',
		reverseRelation: {
			key: 'incidents'
		}
	}, {
		type: Backbone.HasMany,
		key: 'responses',
		relatedModel: 'IncidentResponse',
		reverserRelation: {
			key: 'incidents'
		}
	}]
});

IncidentResponse = Backbone.RelationalModel.extend({
	relations: [{
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: 'IncidentForm',
		reverseRelation: {
			key: 'incident_responses'
		}
	}]
});

Checklist = Backbone.RelationalModel.extend({
	relations: [{
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
		type: Backbone.HasMany,
		key: 'responses',
		relatedModel: 'ChecklistResponse',
		reverseRelation: {
			key: 'checklist'
		}
    }]
});

ChecklistResponse = Backbone.RelationalModel.extend({
	relations: [{
		type: Backbone.HasOne,
		key: 'question',
		relatedModel: 'ChecklistQuestion',
		reverseRelation: {
			key: 'checklist_responses'
		}
	}]
});

ChecklistQuestion = Backbone.RelationalModel.extend({
	relations: [{
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: 'ChecklistForm',
		reverseRelation: {
			key: 'checklist_questions'
		}
	}, {
		type: Backbone.HasOne,
		key: 'type',
		relatedModel: 'ChecklistQuestionType',
		reverseRelation: {
			key: 'checklist_questions'
		}
	}]
});
