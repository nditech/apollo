WebappRouter = Backbone.Router.extend({
   routes: {
       "!/messages": "messages", // #!/messages
       "!/contacts": "contacts", // #!/contacts
   },
   
   messages: function () {
       screen = new Screen({title: 'Message Log', contents: '', link: '#!/messages'});
       screen_view = new ScreenView({model: screen});
       
       paginated_collection = new MessageCollection();
       $('div.full_width_content').html(Templates.MessageSearch);
       
       paginated_collection.fetch({
           success: function (coll, response) {
               msgs_view = new MessageLogView({collection: coll}).render();
               $('div.full_width_content').append(msgs_view);
               
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
           },
       });
   },
   
   contacts: function () {
       screen = new Screen({title: 'Contacts', contents: '', link: '#!/contacts'});
       screen_view = new ScreenView({model: screen});
       
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
           },
       });
   }
});