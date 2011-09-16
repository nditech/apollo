ZambiaRouter = Backbone.Router.extend({
    routes: {
       "": "dashboard", // #!/dashboard
       "!/contacts": "contacts", // #!/contacts
       "!/contact/add": "contact_add", // #!/contact/add
       "!/contact/:id": "contact_edit", // #!/contact/1
       "!/elections/checklists": "checklists", // #!/elections/checklists
       "!/elections/checklist/:id": "checklist_edit", // #!/elections/checklist/1
       "!/elections/incidents": "incidents", // #!/elections/incidents
       "!/elections/incident/add": "incident_add", // #!/elections/incident/add
       "!/elections/incident/:id": "incident_edit", // #!/elections/incident/1
       "!/elections/process_analysis": "process_analysis", // #!/elections/process_analysis
       "!/elections/results_analysis": "results_analysis", // #!/elections/results_analysis
    },

    dashboard: function () {
        screen_model = new Screen({title: 'Dashboard', contents: '', link: '#!/dashboard'});
        screen_view = new ScreenView({model: screen_model, template: 'ZambiaDashboardScreen'});
    },
    
    checklists: function () {
        screen_model = new Screen({title: 'Election Checklists', contents: '', link: '#!/elections/checklists'});
        screen_view = new ScreenView({model: screen_model});

        paginated_collection = new ChecklistCollection();
        $('div.full_width_content').html(Templates.ChecklistFilter);
        
        paginated_collection.fetch({
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
              
              $('.date_field').datepicker({dateFormat: 'yy-mm-dd'});
          },
        });
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
       
       paginated_collection = new IncidentCollection();
       $('div.full_width_content').html(Templates.IncidentFilter);
       
       paginated_collection.fetch({
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