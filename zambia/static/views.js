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
	},
	
	events: {
        "change input.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change #search_location": "autocompleteChanged",
        "submit": "save"
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = field.val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
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

ChecklistEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged", "ecz_status");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "keyup input[name='response.attributes.J']": "ecz_status",
        "radio_click input:radio.field": "radioChanged",
        "submit": "save"
    },
    
    ecz_status: function (e) {
        var value = $(e.currentTarget).val();
        if (value.length == 6) {
            if (value == this.model.get('location').get('parent').get('code')) {
                // ECZ code matches
                $('#ecz_status', this.el).attr('src', '/assets/images/tick.png').show();
            } else {
                $('#ecz_status', this.el).attr('src', '/assets/images/delete.png').show();
            }
        }
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = (field.val() == 0 || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
        self.model.get('response').save(false, {success: function () {
	        setTimeout(function () { history.go(-1); }, 200);
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.ChecklistSectionTabs());
		$(self.el).append(Templates.ChecklistMetadata(this.model.attributes));
		$(self.el).append(Templates.ChecklistEdit(this.model.attributes));
		
		// Initialize values for drop down selections
		_(self.model.get('response').attributes).each(function (value, key) {
		    input_el = $('input[name="response.attributes.'+key+'"]:first', self.el);
		    		    
		    if ($(input_el).attr('type') == 'radio') {
		        $('input[name="response.attributes.'+key+'"][value="'+value+'"]', self.el).attr('checked', 'checked');
		    } else {
		        $('input[name="response.attributes.'+key+'"]', self.el).val(value);
		    }
		});
        
		return self.el;
	}
});

IncidentView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Incident(this.model.attributes));
		return this.el;
	}
});

IncidentCollectionView = Backbone.View.extend({
    tagName: 'table',
    id: 'checklists',
    className: 'datagrid',
    
    events: {
        "click .del_incident": "deleteIncidentDialog",
        "click #del_btn": "deleteIncident",
        "click #del_cancel": "cancelDelete",
    },
    
    deleteIncidentDialog: function (e) {
        var resource_uri = $(e.currentTarget).attr('title');
        $.facebox(Templates.IncidentDelDialog({'resource_uri': resource_uri}))
    },
    
    deleteIncident: function (e) {
        var self = this;
        var resource_uri = $(e.currentTarget).attr('title');
        self.collection.get(resource_uri).destroy({success: function (model, response) {
            $.facebox.close();
            self.collection.fetch();
        }});
    },
    
    cancelDelete: function (e) {
        $.facebox.close();
    },

    render: function(){
        $('#del_btn').die('click');
        $('#del_cancel').die('click');
        
        var self = this;
        // Store the heading of the table so it can be reused
        var heading = $(self.el).children("tbody").children("tr")[0];
        $(self.el).empty();
		$(self.el).append(heading ? heading : Templates.IncidentHeader());
		if (self.collection.length) {
		    self.collection.each(function (mdl) {
    			incident_view = new IncidentView({model: mdl}).render();
    			$(self.el).append(incident_view);
    		});
		} else {
		    $(self.el).children("tbody").append(Templates.IncidentEmpty());
		}
		
		$('#del_btn').live('click', self.deleteIncident);
        $('#del_cancel').live('click', self.cancelDelete);
		
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render", "deleteIncidentDialog", "deleteIncident", "cancelDelete");
        this.collection.bind('reset', this.render);
    },
});

IncidentEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change textarea.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change input:checkbox.field": "radioChanged",
        "radio_click input:radio.field": "radioChanged", // a custom event is monitored to prevent out of order execution
        "submit": "save"
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = (field.val() == 0 || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
        self.model.get('response').save(false, {success: function () {
	        setTimeout(function () { history.go(-1); }, 200);
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.IncidentMetadata(this.model.attributes));
		$(self.el).append(Templates.IncidentEdit(this.model.attributes));
		
		// Initialize values for drop down selections
		_(self.model.get('response').attributes).each(function (value, key) {
		    input_el = $('input[name="response.attributes.'+key+'"]:first', self.el);
		    		    
		    if ($(input_el).attr('type') == 'radio') {
		        $('input[name="response.attributes.'+key+'"][value="'+value+'"]', self.el).attr('checked', 'checked');
		    } else if ($(input_el).attr('type') == 'checkbox') {
		        if (value) {
		            $('input[name="response.attributes.'+key+'"]', self.el).attr('checked', 'checked');
		        }
		    } else {
		        $('input[name="response.attributes.'+key+'"]', self.el).val(value);
		    }
		});
		$('textarea[name="response.attributes.description"]', self.el).val(self.model.get('response').get('description'));
        
		return self.el;
	}
});