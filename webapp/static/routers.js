WebappRouter = Backbone.Router.extend({
   routes: {
       "!/messages": "messages", // #!/messages
       "!/contacts": "contacts", // #!/contacts
   },
   
   messages: function () {
       screen = new Screen({title: 'Message Log', contents: ''});
       screen_view = new ScreenView({model: screen});
       
       paginated_collection = new MessageCollection();
       paginated_collection.fetch({
           success: function (coll, response) {
               msgs_view = new MessageLogView({collection: coll}).render();
               $('div.full_width_content').html(msgs_view);
               $('div.full_width_content').prepend(Templates.MessageSearch);
           },
       });
   },
   
   contacts: function () {
       screen = new Screen({title: 'Contacts', contents: ''});
       screen_view = new ScreenView({model: screen});
       
       paginated_collection = new ContactCollection();
       paginated_collection.fetch({
           success: function (coll, response) {
               contacts_view = new ContactsView({collection: coll}).render();
               $('div.full_width_content').html(contacts_view);
               $('div.full_width_content').prepend(Templates.ContactSearch);
           },
       });
   }
});