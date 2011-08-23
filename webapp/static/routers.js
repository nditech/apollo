WebappRouter = Backbone.Router.extend({
   routes: {
       "!/messages": "messages", // #!/messages
   },
   
   messages: function () {
       screen_model = new Screen({title: 'Message Log', contents: '', link: '#!/messages'});
       screen_view = new ScreenView({model: screen_model});
       
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
   }
});