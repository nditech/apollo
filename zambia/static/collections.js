// Backbone.js Collections
MessageCollection = PaginatedCollection.extend({
    model: Message,
    baseUrl: '/api/v1/message/',
});