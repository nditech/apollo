// Backbone.js Collections

ContactCollection = PaginatedCollection.extend({
	model: Contact,
	baseUrl: '/api/v1/contacts/',
});
