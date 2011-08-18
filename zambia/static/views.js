// Backbone.js views
ChecklistView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Checklist(this.model.attributes));
		return this.el;
	}
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
		self.collection.each(function (mdl) {
			checklist_view = new ChecklistView({model: mdl}).render();
			$(self.el).append(checklist_view);
		});
		return self.el;
    },

    initialize: function(){
        _.bindAll(this, "render");
        this.collection.bind('reset', this.render);
    },
});