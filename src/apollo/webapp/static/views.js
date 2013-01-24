// Backbone.js views
ScreenView = Backbone.View.extend({
	el: 'div#container',
	render: function(){
	    var self = this;
	    // Set document title
	    $('title').html(self.model.get('title') + ' - Apollo');
	    
	    // Highlight the current page link
	    $('#dropmenu li a').removeClass("active");
	    $('#dropmenu li').each(function () {
	        if ($("a", this).attr("href") == self.model.get('link')) {
	            $("a:first", this).addClass("active");
	            
	            // The following will also highlight the parent menu to aid context
	            if ($(this).parent('ul.sub-menu')) {
	                var parent = $(this).parent('ul.sub-menu').parent();
	                $('a:first', parent).addClass('active');
	            }
	        }
	    });
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
    className: 'datagrid',

    render: function(){
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.MessageHeader());
		if (self.collection.length) {
		    self.collection.each(function (mdl) {
    			msg_view = new MessageView({model: mdl}).render();
    			$(self.el).append(msg_view);
    		});
		} else {
		    $(self.el).children("tbody").append(Templates.MessageEmpty());
		}
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});

