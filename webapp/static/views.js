// Backbone.js views
ScreenView = Backbone.View.extend({
	el: 'div#container',
	render: function(){
		$(this.el).html(Templates.Screen(this.model.attributes));
	},
	initialize: function () {
	    _.bindAll(this, 'render');
	    this.render();
	}
});

MessageView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Message(this.model.attributes));
		return this.el;
	}
});

MessageLogView = Backbone.View.extend({
    tagName: 'table',
    id: 'messages',

    render: function(){
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.MessageHeader());
		self.collection.each(function (mdl) {
			msg_view = new MessageView({model: mdl}).render();
			$(self.el).append(msg_view);
		});
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});

ContactView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Contact(this.model.attributes));
		return this.el;
	}
});

ContactsView = Backbone.View.extend({
    tagName: 'table',
    id: 'contacts',

    render: function(){
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.ContactHeader());
		self.collection.each(function (mdl) {
			contact_view = new ContactView({model: mdl}).render();
			$(self.el).append(contact_view);
		});
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});