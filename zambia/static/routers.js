ZambiaRouter = Backbone.Router.extend({
    routes: {
       "": "dashboard", // #!/dashboard
       "!/contacts": "contacts", // #!/contacts
       "!/contact/add": "contact_add", // #!/contact/add
       "!/contact/:id": "contact_edit", // #!/contact/1
       "!/elections/checklists": "checklists", // #!/elections/checklists
       "!/elections/checklist/add": "checklist_add", // #!/elections/checklist/add
       "!/elections/checklist/:id": "checklist_edit", // #!/elections/checklist/1
       "!/elections/incidents": "incidents", // #!/elections/incidents
       "!/elections/incident/add": "incident_add", // #!/elections/incident/add
       "!/elections/incident/:id": "incident_edit", // #!/elections/incident/1
       "!/elections/process_analysis": "process_analysis", // #!/elections/process_analysis
       "!/elections/results_analysis": "results_analysis", // #!/elections/results_analysis
       "!/logout": "user_logout", // #!/logout
    },
    
    user_logout: function () {
        session_clear();
        location.href='/accounts/logout';
    },

    dashboard: function () {
        screen_model = new Screen({title: 'Dashboard', contents: '', link: '#!/dashboard'});
        screen_view = new ScreenView({model: screen_model, template: 'ZambiaDashboardScreen'});
        
        params = {};
        
        update_stats = function (result) {
            setup.missing = result.setup_missing;
            voting.missing = result.voting_missing;
            closing.missing = result.closing_missing;
            counting.missing = result.counting_missing;

            setup.partial = result.setup_partial;
            voting.partial = result.voting_partial;
            closing.partial = result.closing_partial;
            counting.partial = result.counting_partial;

            setup.complete = result.setup_complete;
            voting.complete = result.voting_complete;
            closing.complete = result.closing_complete;
            counting.complete = result.counting_complete;
		}
		
		fetch_stats = function () {
            $.ajax({
    	        url: '/zambia/dashboard_stats/',
    	        data: params,
    	        global: false,
    	        success: function (result) {
    	            update_stats(result);
    	        }
    	    });
        }
        
        var dashboard_view = new DashboardView().render();
        $('div.full_width_content').html(dashboard_view);
        
        var missing_color = "#ff0d00";
        var partial_color = "#fff800";
        var complete_color = "#39e639";
        var text_color = "#000";
        var w = 400;
        var h = 25;
        
        var setup    = {missing: 0, partial: 0, complete: 0};
        var voting   = {missing: 0, partial: 0, complete: 0};
        var closing  = {missing: 0, partial: 0, complete: 0};
        var counting = {missing: 0, partial: 0, complete: 0};
        
        checklists_status =  function () {
        	return {
        		setup: {
        			data: function () { return _(setup).map(function (i) { return [i]; }); }, 
        			total: function () { return _(setup).reduce(function(i, sum) { return sum + i; }); }
        		}, 
        		voting: {
        			data: function () { return _(voting).map(function (i) { return [i]; }); }, 
        			total: function () { return _(voting).reduce(function(i, sum) { return sum + i; }); }
        		},
        		closing: {
        			data: function () { return _(closing).map(function (i) { return [i]; }); }, 
        			total: function () { return _(closing).reduce(function(i, sum) { return sum + i; }); } 
        		},
        		counting: {
        			data: function () { return _(counting).map(function (i) { return [i]; }); }, 
        			total: function () { return _(counting).reduce(function(i, sum) { return sum + i; }); } 
        		},
        	};
        }
        
        vis_setup = new pv.Panel().canvas('setup').width(w+10).height(h).bottom(h).left(0).right(0);
        vis_setup.add(pv.Layout.Stack)
            .layers(checklists_status().setup.data)
            .y(function (d) { return d / checklists_status().setup.total() * w; })
            .orient('left-top')
            .layer.add(pv.Bar)
                .fillStyle(pv.colors(missing_color,partial_color,complete_color).by(function () { return this.parent.index; }))
                .anchor("left").add(pv.Label).textStyle(text_color).text(function(d) { return (d / checklists_status().setup.total() * 100).toFixed(1) + '%'; }).visible(function (d) { return d / checklists_status().setup.total() > 0.1;});

        vis_setup.add(pv.Label).textStyle(text_color).text(function () { return 'Missing: '+ checklists_status().setup.data()[0][0]; }).top(h*1.8).left(0);
        vis_setup.add(pv.Label).textStyle(text_color).text(function () { return 'Partial: '+ checklists_status().setup.data()[1][0]; }).top(h*1.8).left(100);
        vis_setup.add(pv.Label).textStyle(text_color).text(function () { return 'Complete: '+ checklists_status().setup.data()[2][0]; }).top(h*1.8).left(200);

        vis_voting = new pv.Panel().canvas('voting').width(w+10).height(h).bottom(h).left(0).right(0);
        vis_voting.add(pv.Layout.Stack)
            .layers(checklists_status().voting.data)
            .y(function (d) { return d / checklists_status().voting.total() * w; })
            .orient('left-top')
            .layer.add(pv.Bar)
                .fillStyle(pv.colors(missing_color,partial_color,complete_color).by(function () { return this.parent.index; }))
                .anchor("left").add(pv.Label).textStyle(text_color).text(function(d) { return (d / checklists_status().setup.total() * 100).toFixed(1) + '%'; }).visible(function (d) { return d / checklists_status().voting.total() > 0.1;});

        vis_voting.add(pv.Label).textStyle(text_color).text(function () { return 'Missing: '+ checklists_status().voting.data()[0][0]; }).top(h*1.8).left(0);
        vis_voting.add(pv.Label).textStyle(text_color).text(function () { return 'Partial: '+ checklists_status().voting.data()[1][0]; }).top(h*1.8).left(100);
        vis_voting.add(pv.Label).textStyle(text_color).text(function () { return 'Complete: '+ checklists_status().voting.data()[2][0]; }).top(h*1.8).left(200);

        vis_closing = new pv.Panel().canvas('closing').width(w+10).height(h).bottom(h).left(0).right(0);
        vis_closing.add(pv.Layout.Stack)
            .layers(checklists_status().closing.data)
            .y(function (d) { return d / checklists_status().closing.total() * w; })
            .orient('left-top')
            .layer.add(pv.Bar)
                .fillStyle(pv.colors(missing_color,partial_color,complete_color).by(function () { return this.parent.index; }))
                .anchor("left").add(pv.Label).textStyle(text_color).text(function(d) { return (d / checklists_status().setup.total() * 100).toFixed(1) + '%'; }).visible(function (d) { return d / checklists_status().closing.total() > 0.1;});

        vis_closing.add(pv.Label).textStyle(text_color).text(function () { return 'Missing: '+ checklists_status().closing.data()[0][0]; }).top(h*1.8).left(0);
        vis_closing.add(pv.Label).textStyle(text_color).text(function () { return 'Partial: '+ checklists_status().closing.data()[1][0]; }).top(h*1.8).left(100);
        vis_closing.add(pv.Label).textStyle(text_color).text(function () { return 'Complete: '+ checklists_status().closing.data()[2][0]; }).top(h*1.8).left(200);

        vis_counting = new pv.Panel().canvas('counting').width(w+10).height(h).bottom(h).left(0).right(0);
        vis_counting.add(pv.Layout.Stack)
            .layers(checklists_status().counting.data)
            .y(function (d) { return d / checklists_status().counting.total() * w; })
            .orient('left-top')
            .layer.add(pv.Bar)
                .fillStyle(pv.colors(missing_color,partial_color,complete_color).by(function () { return this.parent.index; }))
                .anchor("left").add(pv.Label).textStyle(text_color).text(function(d) { return (d / checklists_status().setup.total() * 100).toFixed(1) + '%'; }).visible(function (d) { return d / checklists_status().counting.total() > 0.1;});

        vis_counting.add(pv.Label).textStyle(text_color).text(function () { return 'Missing: '+ checklists_status().counting.data()[0][0]; }).top(h*1.8).left(0);
        vis_counting.add(pv.Label).textStyle(text_color).text(function () { return 'Partial: '+ checklists_status().counting.data()[1][0]; }).top(h*1.8).left(100);
        vis_counting.add(pv.Label).textStyle(text_color).text(function () { return 'Complete: '+ checklists_status().counting.data()[2][0]; }).top(h*1.8).left(200);

        vis_setup.render();
        vis_voting.render();
        vis_closing.render();
        vis_counting.render();

        // set frequency to redraw the charts
        setInterval(function () { vis_setup.render(); },    1000);
        setInterval(function () { vis_voting.render(); },   1000);
        setInterval(function () { vis_closing.render(); },  1000);
        setInterval(function () { vis_counting.render(); }, 1000);

        // set frequency for fetching data
        setInterval(function () { fetch_stats(); }, 1000);
    },
    
    checklists: function () {
        screen_model = new Screen({title: 'Election Checklists', contents: '', link: '#!/elections/checklists'});
        screen_view = new ScreenView({model: screen_model});
        
        var search_options = {};

        paginated_collection = new ChecklistCollection();
        $('div.full_width_content').html(Templates.ChecklistFilter);
        
        // Autocomplete for location input textbox
        $("#location__id").catcomplete({
            source: '/api/v1/location/search/',
            position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
            focus: function (event, ui) {
                //$('#location__id').val(ui.item.name);
                return false;
            },
            select: function (event, ui) {
                $('#location__id').val(ui.item.name);
                $('#search_location__id').val(ui.item.id);
                return false;
            }
        });
        
        $.each($('.persist'), function (idx, el) {
            session_val = session_getitem('checklist-'+$(el).attr('id'));
            $(el).val(session_val);
            match = /^search_(.*)/.exec($(el).attr('id'));
            if (session_val && match){
                search_options[match[1]] = session_val;
            }
        });
                
        paginated_collection.filtrate(search_options, {
          success: function (coll, response) {
              checklists_view = new ChecklistCollectionView({collection: coll}).render();
              $('div.full_width_content').append(checklists_view);
              $('div.full_width_content').append('<div class="pagination" id="pager"></div>');
              $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
              $('.pagination').bind('paginate', function (event, page) {
                 coll.gotoPage(page);
                 return false;
              });

              coll.bind('reset', function (event) {
                 $('.pagination').unbind('paginate');
                 $('.pagination').paginator('destroy');
                 $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
                 $.scrollTo('div#container', 400);
                 $('.pagination').bind('paginate', function (event, page) {
                     coll.gotoPage(page);
                     return false;
                 });
              });
              
              $("#location__id").blur(function () {
                  if (!$(this).val()) {
                      $('#search_location__id').val("");
                  }
              });
              
              $('.date_field').datepicker({dateFormat: 'yy-mm-dd'});
              $('#form_add_checklist').click(function () {
                   location.href = '/#!/elections/checklist/add';
              });
          },
        });
   },
   
   checklist_add: function () {
       screen_model = new Screen({title: 'Add Checklist', content: '', link: '#!/elections/checklist/add'});
       screen_view = new ScreenView({model: screen_model});

       checklist = new Checklist();
       // Since this is a new incident object, we need to explicitly set the IncidentResponse object
       var checklist_response = new ChecklistResponse();
       // Also set the form explicitly
       checklist.set({'response': checklist_response});
       checklist.attributes.form = '/api/v1/checklist_form/1';
       
       checklist_add_view = new ChecklistAddView({model: checklist}).render();
       $('div.full_width_content').html(checklist_add_view);
       $('div.pane:first').show();
   },
   
   checklist_edit: function (id) {
        screen_model = new Screen({title: 'Edit Checklist', content: '', link: '#!/elections/checklist/' + id});
        screen_view = new ScreenView({model: screen_model});

        checklist = new Checklist();
        checklist.id = '/api/v1/checklist/' + id;
        checklist.fetch({
            success: function (model, response) {
                checklist_edit_view = new ChecklistEditView({model: model}).render();
                $('div.full_width_content').html(checklist_edit_view);
                $('div.pane:first').show();
            }
        });
   },
   
   incidents: function () {
       screen_model = new Screen({title: 'Election Incidents', contents: '', link: '#!/elections/incidents'});
       screen_view = new ScreenView({model: screen_model});
       
       var search_options = {};
       
       paginated_collection = new IncidentCollection();
       $('div.full_width_content').html(Templates.IncidentFilter);
       
        // Autocomplete for location input textbox
        $("#location__id").catcomplete({
            source: '/api/v1/location/search/',
            position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
            select: function (event, ui) {
                $('#location__id').val(ui.item.name);
                $('#search_location__id').val(ui.item.id);
                return false;
            }
        });
        
        $.each($('.persist'), function (idx, el) {
            session_val = session_getitem('incident-'+$(el).attr('id'));
            $(el).val(session_val);
            match = /^search_(.*)/.exec($(el).attr('id'));
            if (session_val && match){
                search_options[match[1]] = session_val;
            }
        });
       
       paginated_collection.filtrate(search_options, {
         success: function (coll, response) {
             incidents_view = new IncidentCollectionView({collection: coll}).render();
             $('div.full_width_content').append(incidents_view);
             $('div.full_width_content').append('<div class="pagination" id="pager"></div>');
             $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
             $('.pagination').bind('paginate', function (event, page) {
                coll.gotoPage(page);
                return false;
             });

             coll.bind('reset', function (event) {
                $('.pagination').unbind('paginate');
                $('.pagination').paginator('destroy');
                $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
                $.scrollTo('div#container', 400);
                $('.pagination').bind('paginate', function (event, page) {
                    coll.gotoPage(page);
                    return false;
                });
             });
             
             $("#location__id").blur(function () {
                 if (!$(this).val()) {
                     $('#search_location__id').val("");
                 }
             });
             
             $('.date_field').datepicker({dateFormat: 'yy-mm-dd'});
             $('#form_add_incident').click(function () {
                 location.href = '/#!/elections/incident/add';
             });
         },
       });
   },
   
   incident_edit: function (id) {
       screen_model = new Screen({title: 'Edit Incident', content: '', link: '#!/elections/incident/' + id});
       screen_view = new ScreenView({model: screen_model});

       incident = new Incident();
       incident.id = '/api/v1/incident/' + id;
       incident.fetch({
           success: function (model, response) {
                incident_edit_view = new IncidentEditView({model: model}).render();
                $('div.full_width_content').html(incident_edit_view);
               
                // Autocomplete for location input textbox
                $("#monitor_id").catcomplete({
                    source: '/api/v1/contacts/search/',
                    position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
                    focus: function (event, ui) {
                        //$('#monitor_id').val(ui.item.observer_id);
                        return false;
                    },
                    select: function (event, ui) {
                        $('#observer_name').html(ui.item.name);
                        $('#monitor_id').val(ui.item.observer_id);
                        $('#observer_id').val(ui.item.resource_uri).trigger('change');
                        return false;
                    }
                });

                $("#monitor_id").blur(function () {
                    if (!$(this).val()) {
                        $('#observer_id').val("");
                    }
                });
           }
       });
   },
   
   incident_add: function (id) {
       screen_model = new Screen({title: 'Add Incident', content: '', link: '#!/elections/incident/add'});
       screen_view = new ScreenView({model: screen_model});
       
       incident = new Incident();
       
       // Since this is a new incident object, we need to explicitly set the IncidentResponse object
       var incident_response = new IncidentResponse();
       // Also set the form explicitly
       incident.set({'response': incident_response});
       incident.attributes.form = '/api/v1/incident_form/1';
       
       incident_add_view = new IncidentAddView({model: incident}).render();
       $('div.full_width_content').html(incident_add_view);
      
       // Autocomplete for location input textbox
       $("#monitor_id").catcomplete({
           source: '/api/v1/contacts/search/',
           position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
           focus: function (event, ui) {
               //$('#monitor_id').val(ui.item.observer_id);
               return false;
           },
           select: function (event, ui) {
               $('#observer_name').html(ui.item.name);
               $('#monitor_id').val(ui.item.observer_id);
               $('#observer_id').val(ui.item.resource_uri).trigger('change');
               return false;
           }
       });

       $("#monitor_id").blur(function () {
           if (!$(this).val()) {
               $('#observer_id').val("");
           }
       });
   },
   
   process_analysis: function () {
       screen_model = new Screen({title: 'Election Process Analysis', contents: '', link: '#!/elections/process_analysis'});
       screen_view = new ScreenView({model: screen_model});
   },
   
   results_analysis: function () {
       screen_model = new Screen({title: 'Election Results Analysis', contents: '', link: '#!/elections/results_analysis'});
       screen_view = new ScreenView({model: screen_model});
   },
   
   contacts: function () {
          screen_model = new Screen({title: 'Contacts', contents: '', link: '#!/contacts'});
          screen_view = new ScreenView({model: screen_model});
          
          paginated_collection = new ContactCollection();
          $('div.full_width_content').html(Templates.ContactSearch);

          paginated_collection.fetch({
               success: function (coll, response) {
                   contacts_view = new ContactsView({collection: coll}).render();
                   $('div.full_width_content').append(contacts_view);

                   $('div.full_width_content').append('<div class="pagination" id="pager"></div>');
                   $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
                   $('.pagination').bind('paginate', function (event, page) {
                      coll.gotoPage(page);
                      return false;
                   });

                   coll.bind('reset', function (event) {
                      $('.pagination').unbind('paginate');
                      $('.pagination').paginator('destroy');
                      $('.pagination').paginator({currentPage: coll.pageInfo().page, pages: coll.pageInfo().pages});
                      $.scrollTo('div#container', 400);
                      $('.pagination').bind('paginate', function (event, page) {
                          coll.gotoPage(page);
                          return false;
                      });
                   });

                   // Autocomplete for location input textbox
                   $("#location__id").catcomplete({
                       source: '/api/v1/location/search/',
                       position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
                       focus: function (event, ui) {
                           //$('#location__id').val(ui.item.name);
                           return false;
                       },
                       select: function (event, ui) {
                           $('#location__id').val(ui.item.name);
                           $('#search_location__id').val(ui.item.id);
                           return false;
                       }
                   });

                   $("#location__id").blur(function () {
                       if (!$(this).val()) {
                           $('#search_location__id').val("");
                       }
                   });
              },
          });
          
          $('#form_add_contact').click(function () {
              location.href = '/#!/contact/add';
          });
      },
      
      contact_edit: function (id) {
          // Save page contents elsewhere before replacing it
          screen_model = new Screen({title: 'Edit Contact', content: '', link: '#!/contact/' + id});
          screen_view = new ScreenView({model: screen_model});
          
          contact = new Contact();
          contact.id = '/api/v1/contact/' + id;
          contact.fetch({
              success: function (model, response) {
                  contact_edit_view = new ContactEditView({model: model}).render();
                  $('div.full_width_content').html(contact_edit_view);
              }
          });
      },
      
    contact_add: function () {
        // Save page contents elsewhere before replacing it
        screen_model = new Screen({title: 'Add Contact', content: '', link: '#!/contact/add'});
        screen_view = new ScreenView({model: screen_model});

        contact = new Contact();
        contact_add_view = new ContactAddView({model: contact}).render();
        $('div.full_width_content').html(contact_add_view);
    }
});