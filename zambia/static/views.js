// Backbone.js views
MessageView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.render();
	},
	
	render: function () {
		$(this.el).html(Templates.Message(this.model.attributes));
		return this;
	}
});

MessageLogView = Backbone.View.extend({
    el: 'table#messages',

    render: function(){
		$('table#messages').empty();
		$('table#messages').append('<tr><th>Contact</th><th>Connection</th><th>Direction</th><th>Date</th><th>Text</th></tr>');
		this.collection.each(function (mdl) {
			msg_view = new MessageView({model: mdl}).el;
			$('table#messages').append(msg_view);
		});
		$(window).scrollTop(200);
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
		this.render();
    },
});