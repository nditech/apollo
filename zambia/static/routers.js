ZambiaRouter = Backbone.Router.extend({
    routes: {
       "": "dashboard", // #!/dashboard
       "!/elections/checklists": "checklists", // #!/elections/checklists
       "!/elections/incidents": "incidents", // #!/elections/incidents
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
                     $('#location__id').val(ui.item.label);
                     return false;
                 },
                 select: function (event, ui) {
                     $('#location__id').val(ui.item.label);
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
   
   incidents: function () {
       screen_model = new Screen({title: 'Election Incidents', contents: '', link: '#!/elections/incidents'});
       screen_view = new ScreenView({model: screen_model});
   },
   
   process_analysis: function () {
       screen_model = new Screen({title: 'Election Process Analysis', contents: '', link: '#!/elections/process_analysis'});
       screen_view = new ScreenView({model: screen_model});
   },
   
   results_analysis: function () {
       screen_model = new Screen({title: 'Election Results Analysis', contents: '', link: '#!/elections/results_analysis'});
       screen_view = new ScreenView({model: screen_model});
   },
});