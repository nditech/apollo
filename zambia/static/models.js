// Backbone.js models
Contact = Backbone.RelationalModel.extend();
Backend = Backbone.RelationalModel.extend();

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

Message = Backbone.RelationalModel.extend({
    relations: [{
		type: Backbone.HasOne,
		key: 'connection',
		relatedModel: 'Connection',
		reverseRelation: {
			key: 'messages',
		}
	},{
	    type: Backbone.HasOne,
	    key: 'contact',
	    relatedModel: 'Contact',
	    reverseRelation: {
	        key: 'messages'
	},
	}]
});
