// Backbone.js models

Contact = Backbone.RelationalModel.extend({
    urlRoot: '/api/v1/contact/',
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
        relatedModel: 'Contact',
        includeInJSON: 'resource_uri'
    },{
        type: Backbone.HasOne,
        key: 'location',
        relatedModel: 'Location',
        includeInJSON: 'resource_uri'
    }]
});
