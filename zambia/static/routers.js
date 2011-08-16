ZambiaRouter = Backbone.Router.extend({
    routes: {
       "!/dashboard": "dashboard", // #!/dashboard
       "!/elections/checklists": "checklists", // #!/elections/checklists
       "!/elections/incidents": "incidents", // #!/elections/incidents
       "!/elections/process_analysis": "process_analysis", // #!/elections/process_analysis
       "!/elections/results_analysis": "results_analysis", // #!/elections/results_analysis
    },

    dashboard: function () {
        screen = new Screen({title: 'Dashboard', contents: '', link: '#!/dashboard'});
        screen_view = new ScreenView({model: screen, template: 'DashboardScreen'});
    },
    
    checklists: function () {
        screen = new Screen({title: 'Election Checklists', contents: '', link: '#!/elections/checklists'});
        screen_view = new ScreenView({model: screen});

        paginated_collection = new ChecklistCollection();
        paginated_collection.fetch({
          success: function (coll, response) {
              //checklists_view = new ChecklistCollectionView({collection: coll}).render();
              //$('div.full_width_content').html(checklists_view);
              //$('div.full_width_content').prepend(Templates.ChecklistSearch);
          },
        });
   },
   
   incidents: function () {
       screen = new Screen({title: 'Election Incidents', contents: '', link: '#!/elections/incidents'});
       screen_view = new ScreenView({model: screen});
   },
   
   process_analysis: function () {
       screen = new Screen({title: 'Election Process Analysis', contents: '', link: '#!/elections/process_analysis'});
       screen_view = new ScreenView({model: screen});
   },
   
   results_analysis: function () {
       screen = new Screen({title: 'Election Results Analysis', contents: '', link: '#!/elections/results_analysis'});
       screen_view = new ScreenView({model: screen});
   },
});