// Backbone.js models
Role = Backbone.RelationalModel.extend();

Contact = Backbone.RelationalModel.extend({
    urlRoot: '/api/v1/contact/',
    relations: [{
        type: Backbone.HasMany,
		key: 'connections',
		relatedModel: 'Connection',
		reverserRelation: {
			key: 'contact'
		}
    },{
        type: Backbone.HasOne,
        key: 'supervisor',
        relatedModel: 'Contact',
        includeInJSON: 'resource_uri'
    },{
        type: Backbone.HasOne,
        key: 'role',
        relatedModel: 'Role',
        includeInJSON: 'resource_uri'
    },
    {
        type: Backbone.HasOne,
        key: 'location',
        relatedModel: 'Location',
        includeInJSON: 'resource_uri'
    }]
});

Backend = Backbone.RelationalModel.extend();

Connection = Backbone.RelationalModel.extend({
    urlRoot: '/api/v1/connection/',
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
