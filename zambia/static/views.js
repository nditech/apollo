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

ChecklistCollectionView = Backbone.View.extend({
    tagName: 'table',
    id: 'checklists',
    className: 'datagrid',
    
    events: {
        "click .del_checklist": "deleteChecklistDialog",
        "click #del_btn": "deleteChecklist",
        "click #del_cancel": "cancelDelete",
    },
    
    deleteChecklistDialog: function (e) {
        var resource_uri = $(e.currentTarget).attr('title');
        $.facebox(Templates.ChecklistDelDialog({'resource_uri': resource_uri}))
    },
    
    deleteChecklist: function (e) {
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
		$(self.el).append(heading ? heading : Templates.ChecklistHeader());
		if (self.collection.length) {
		    self.collection.each(function (mdl) {
    			checklist_view = new ChecklistView({model: mdl}).render();
    			$(self.el).append(checklist_view);
    		});
		} else {
		    $(self.el).children("tbody").append(Templates.ChecklistEmpty());
		}
		
		$('#del_btn').live('click', self.deleteChecklist);
        $('#del_cancel').live('click', self.cancelDelete);
		
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render", "deleteChecklistDialog", "deleteChecklist", "cancelDelete");
        this.collection.bind('reset', this.render);
    },
});

IncidentCollectionView = Backbone.View.extend({
    tagName: 'table',
    id: 'incidents',
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