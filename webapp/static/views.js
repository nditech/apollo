// Backbone.js views
ScreenView = Backbone.View.extend({
	el: 'div#container',
	render: function(){
	    // Set document title
	    $('title').html(this.model.get('title') + ' - Apollo');
		$(this.el).html(Templates[this.options.template](this.model.attributes));
	},
	initialize: function () {
	    _.bindAll(this, 'render');
	    // This allows the specification of template when initializing this view
	    // this is useful for screens like the dashboard
	    this.options.template = typeof(this.options.template) == 'undefined' ? 'Screen' : this.options.template;
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