// Backbone.js views
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

ContactEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "autocompleteChanged");
		//this.model.bind('change', this.render);
	},
	
	events: {
        "change input.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change #search_location": "autocompleteChanged",
        "submit": "save"
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val();
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        eval('this.model.attributes.'+field.attr('id')+' = field.val()');
    },
    
    autocompleteChanged: function (e) {
        var field = $(e.currentTarget);
        var data = {};
        match = /^search_(.*)/.exec(field.attr('id'));
		if (match) {
		    if (field.val()) {
		        data[match[1]] = field.val();
		    } else {
		        data[match[1]] = this.model.previous(match[1]);
		    }
			this.model.attributes[match[1]] = data[match[1]];
		}
    },
    		
	save: function () {
	    var self = this;
	    self.model.attributes.connections.models[0].save(false, {success: function () {
	        self.model.save(false, {success: function () {
    	        history.go(-1);
    	    }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
		$(self.el).html(Templates.ContactEdit(this.model.attributes));
		
		// Initialize values for drop down selections
		$('#partner', self.el).val(self.model.get('partner'));
		$('#role', self.el).val(self.model.get('role'));
		$('#gender', self.el).val(self.model.get('gender'));
		$('#cell_coverage', self.el).val(self.model.get('cell_coverage'));
		
		// Autocomplete for location input textbox
        $("#location", self.el).catcomplete({
            source: '/api/v1/location/search/',
            position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
            focus: function (event, ui) {
                $('#location').val(ui.item.label);
                return false;
            },
            select: function (event, ui) {
                $('#search_location').val(ui.item.resource_uri);
                $('#location').val(ui.item.label);
                $('#search_location').change();
                
                return false;
            }
        });

        $("#location", self.el).blur(function () {
            if (!$(this).val()) {
                $('#search_location', self.el).val("");
            }
            $('#search_location').change();
        });
        
		return self.el;
	}
});

ContactsView = Backbone.View.extend({
    tagName: 'table',
    id: 'contacts',
    className: 'datagrid',

    render: function(){
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.ContactHeader());
		if (self.collection.length) {
		    self.collection.each(function (mdl) {
    			contact_view = new ContactView({model: mdl}).render();
    			$(self.el).append(contact_view);
    		});
		} else {
		    $(self.el).children("tbody").append(Templates.ContactEmpty());
		}
		
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});

ChecklistView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Checklist(this.model.attributes));
		return this.el;
	}
});

ChecklistCollectionView = Backbone.View.extend({
    tagName: 'table',
    id: 'checklists',
    className: 'datagrid',

    render: function(){
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.ChecklistHeader());
		if (self.collection.length) {
		    self.collection.each(function (mdl) {
    			checklist_view = new ChecklistView({model: mdl}).render();
    			$(self.el).append(checklist_view);
    		});
		} else {
		    $(self.el).children("tbody").append(Templates.ChecklistEmpty());
		}
		
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});