WebappRouter = Backbone.Router.extend({
   routes: {
       "!/messages": "messages", // #!/messages
       "!/contacts": "contacts", // #!/contacts
   },
   
   messages: function () {
       screen = new Screen({title: 'Message Log', contents: ''});
       screen_view = new ScreenView({model: screen});
       
       msgs = new MessageCollection();
       msgs.fetch({
           success: function (collection, response) {
               msgs_view = new MessageLogView({collection: collection}).render();
               $('div.full_width_content').html(msgs_view);
           },
       });
   },
   
   contacts: function () {
       screen = new Screen({title: 'Contacts', contents: ''});
       screen_view = new ScreenView({model: screen});
       
       contacts = new ContactCollection();
       contacts.fetch({
           success: function (collection, response) {
               contacts_view = new ContactsView({collection: collection}).render();
               $('div.full_width_content').html(contacts_view);
           },
       });
   }
});