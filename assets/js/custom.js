// application specific
$(function () {
    // AJAX throbber for indicating AJAX activity
    $("#throbber").throbber({
	    bgopacity: 0, fgcolor: "#AAA", segments: 12,
		path: function(i, segments) {
			return "M 40,8 c -4,0 -8,-4 -8,-8 c 0,-4 4,-8 8,-8 l 30,0 c 4,0 8,4 8,8 c 0,4 -4,8 -8,8 l -30,0 z";
		},
		opacity: function(i, segments) { return 1-(i%segments)/segments;},
		speed: 3,
		show: function() { $(this).fadeIn(100);},
		hide: function(callback) { $(this).fadeOut(100, callback);}
	});
	
	$(document).ajaxStart(function () { $("#throbber").throbber('enable'); });
	$(document).ajaxComplete(function () { $("#throbber").throbber('disable'); });
	
	$("#throbber").throbber('disable');
	
	// Search
	$('form#search').live('submit', function () {
		search_options = {};
		
		$.each($('.search_field'), function (idx, el) {
			match = /^search_(.*)/.exec($(el).attr('id'));
			if (match && $(el).val()) {
				search_options[match[1]] = $(el).val();
			}
		});
		
		paginated_collection.filtrate(search_options);
		return false;
	});
	
	// Filter dropper
	$("div#filter_dropper").live('click', function () {
		filter_toggle = typeof(filter_toggle) == 'undefined' ? 0 : !filter_toggle;
		if (filter_toggle) {
			$("div#filter").slideUp();
		} else {
			$("div#filter").slideDown();
		}
	});
	
	// Column Sorting
	$("a.sortable_column").live('click', function () {
		match = /^sort_(.*)$/.exec($(this).attr('id'));
		if (match) {
			sort_field = match[1];
			if (paginated_collection.sort_field) {
				match = /^-?(.*)$/.exec(paginated_collection.sort_field);
				if (match && match[1] == sort_field) {
					desc_match = /^-.*$/.exec(paginated_collection.sort_field);
					if (!desc_match) {
						// display descending order image
						$('img.sorted_direction').remove();
						$(this).after('<img src="/assets/images/sort_desc.png" class="sorted_direction" />');

						// Switch to descending order
						paginated_collection.sort_by('-'+sort_field);			
						return false;
					}
				}
			}
			
			// display ascending order image
			$('img.sorted_direction').remove();
			$(this).after('<img src="/assets/images/sort_asc.png" class="sorted_direction" />');
			
			paginated_collection.sort_by(sort_field);
		}
		return false;
	});

    $.widget("custom.catcomplete", $.ui.autocomplete, {
        _create: function () {
            var element_id = this.element.attr('id');
            this.element.after('<input type="hidden" class="search_field" id="search_'+element_id+'" />');
            $.ui.autocomplete.prototype._create.apply(this);
        },
    	_renderMenu: function( ul, items ) {
    		var self = this,
    			currentCategory = "";
    		$.each( items, function( index, item ) {
    			if ( item.category != currentCategory ) {
    				ul.append( "<li class='ui-menu-item ui-autocomplete-category'>" + item.category + "</li>" );
    				currentCategory = item.category;
    			}
    			self._renderItem( ul, item );
    		});
    	}
    });
});