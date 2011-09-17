// Backbone.js views
DashboardView = Backbone.View.extend({
       tagName: 'div',
       
       initialize: function () {
           _.bindAll(this, "render", "search", "resetForm");
       },
       
       events: {
           "change .location_select": "locationChanged",
           "click #form_reset": "resetForm",
           "submit": "search"
       },
       
       resetForm: function () {
           $("select[title='province']").val("");
           $("select[title='district']").html('<option value="">- Select a province -</option>');
           $("select[title='sample']").val("");
           $(this.el).trigger('submit');
           return false;
       },
       
       search: function (e) {
           var self = this;
           var params = {};
           $(".search_field").each(function (index, field) {
               if ($(field).val()) {
                   params[$(field).attr('title')] = $('option:selected', field).attr('title');
               }
           });
           $.get('/zambia/dashboard_stats/', params, function (result) {
               $('#setup_missing', this.el).html(result.setup_missing);
               $('#voting_missing', this.el).html(result.voting_missing);
               $('#closing_missing', this.el).html(result.closing_missing);
               $('#counting_missing', this.el).html(result.counting_missing);
               
               $('#setup_partial', this.el).html(result.setup_partial);
               $('#voting_partial', this.el).html(result.voting_partial);
               $('#closing_partial', this.el).html(result.closing_partial);
               $('#counting_partial', this.el).html(result.counting_partial);
               
               $('#setup_complete', this.el).html(result.setup_complete);
               $('#voting_complete', this.el).html(result.voting_complete);
               $('#closing_complete', this.el).html(result.closing_complete);
               $('#counting_complete', this.el).html(result.counting_complete);
           });
           return false;
       },
       
       locationChanged: function (e) {
           var el = $(e.currentTarget);
           var location_type = $(el).attr("title");
           var id = $('option:selected', el).attr('title');

           if (id) {
               if (location_type == 'province') {
                   $('.location_select').not(el).html('');

                   var districts = new LocationCollection();
                   districts.filtrate({'type__name': 'District', 'parent__id': id}, {
                       success: function (coll, response) {
                           $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models}));
                           $('select[title="district"] option:first').html('- District -');
                       }
                   });
               }
           }
       },
       
       render: function () {           
            $(this.el).html(Templates.ZambiaDashboardFilter());
            $(this.el).append(Templates.ZambiaDashboard());

            var provinces = new LocationCollection();
            provinces.filtrate({'type__name':'Province'}, {
              success: function (coll, response) {
                  $('select[title="province"]').html(Templates.LocationOptions({'locations':coll.models}));
                  $('select[title="province"] option:first').html('- Province -');
              }
            });
            
            $.get('/zambia/dashboard_stats/', function (result) {
                $('#setup_missing', this.el).html(result.setup_missing);
                $('#voting_missing', this.el).html(result.voting_missing);
                $('#closing_missing', this.el).html(result.closing_missing);
                $('#counting_missing', this.el).html(result.counting_missing);
                
                $('#setup_partial', this.el).html(result.setup_partial);
                $('#voting_partial', this.el).html(result.voting_partial);
                $('#closing_partial', this.el).html(result.closing_partial);
                $('#counting_partial', this.el).html(result.counting_partial);
                
                $('#setup_complete', this.el).html(result.setup_complete);
                $('#voting_complete', this.el).html(result.voting_complete);
                $('#closing_complete', this.el).html(result.closing_complete);
                $('#counting_complete', this.el).html(result.counting_complete);
            });

            return this.el;
       }
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