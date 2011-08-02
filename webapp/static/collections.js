// Backbone.js Collections
MessageCollection = PaginatedCollection.extend({
    model: Message,
    baseUrl: '/api/v1/message/',
});

LocationCollection = Backbone.Collection.extend({
	model: Location,
	baseUrl: '/api/v1/location/',
});

IncidentCollection = PaginatedCollection.extend({
	model: Incident,
	baseUrl: '/api/v1/incident/',
});

ContactCollection = PaginatedCollection.extend({
	model: Contact,
	baseUrl: '/api/v1/contact/',
});

ChecklistCollection = PaginatedCollection.extend({
	model: Checklist,
	baseUrl: '/api/v1/checklist/',
});