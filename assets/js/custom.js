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
	
	// Form reset
	$('#form_reset').live('click', function () {
	    $('form#search .input_smoke').each(function () { $(this).val(""); });
	    $('form#search').submit();
	});
	
	// Filter dropper
	$("div#filter_dropper").live('click', function () {
		filter_toggle = typeof(filter_toggle) === 'undefined' ? 0 : !filter_toggle;
		if (filter_toggle) {
			$("div#filter").slideUp();
			$(this).toggleClass('down');
		} else {
			$("div#filter").slideDown();
			$(this).toggleClass('down');
		}
	});
	
	// Facebox
	$('a.sms_sender').live('click', function () {
		$.facebox(Templates.SMSBlaster());
		$('.message').maxlength(457);
	});
	
	// SMS Sending
	$('#send_btn').live('click', function () {
	   $('#send_indicator').show();
	   $('#send_btn').attr('disabled', 'disabled');
	   $('#send_btn_wrapper').addClass('disabled');
	   
	   // Determine the filter options and collection type
	   var params = paginated_collection.filter_options;
	   if (paginated_collection instanceof ChecklistCollection) {
	       params.collection_type = 'checklist';
	   } else if (paginated_collection instanceof IncidentCollection) {
	       params.collection_type = 'incident';
	   } else if (paginated_collection instanceof ContactCollection) {
	       params.collection_type = 'contact';
	   }
	   
	   params.message = $('#message').val();
	   
	   $.post("/sendsms", params);
	   
	   setTimeout(function () {
	      $('#send_indicator').hide();
   	      
   	      $('#send_status').html('Sent successfully!').css('display', 'inline-block').css('color', '#569700');
   	      setTimeout(function () {
   	          $('#send_btn').removeAttr('disabled');
         	  $('#send_btn_wrapper').removeClass('disabled');
         	  $.facebox.close();
   	      }, 2000);
   	      
   	      /*$('#send_status').html('Sending failed! Pls try again.').css('display', 'inline-block').css('color', '#FF0700');
   	      setTimeout(function () {
     	      $('#send_btn').removeAttr('disabled');
           	  $('#send_btn_wrapper').removeClass('disabled');
           	  $('#send_status').fadeOut();
          }, 2000);*/
	   }, 3000);
	});
	
	// Sectional Tabs
	$("div.section_tabs a").live('click', function () {
		var id = $(this).attr('id');
		match = /tab(\d)/.exec(id);
		if (match) {
			$('div.pane').hide();
			$('div#pane' + match[1]).show();
			$.scrollTo('div#wrapper', 400);
		}
	});
	$('div.section_tabs li').live('click', function(){
	    $('div.section_tabs li[title="'+$(this).attr('title')+'"]').addClass('current');
		$('div.section_tabs li').not($('div.section_tabs li[title="'+$(this).attr('title')+'"]')).removeClass('current');
	});
	
	// Uncheck a radio button if clicked twice	
	$('input:radio').live('change', function () {
	    $(this).attr('is_undue', '1');
	}).live('click', function () {
	    if (!$(this).attr('is_undue')) {
	        $(this).removeAttr('checked');
	    } else {
	        $(this).removeAttr('is_undue');
	    }
	    $(this).trigger('radio_click');
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
            this.element.after('<input type="hidden" class="search_field input_smoke" id="search_'+element_id+'" />');
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
    
    $.widget("ui.paginator", {
    	_create: function() {
    		var o = this.options, e = this.element, self = this;
    		e.removeClass('pagination');
    		e.addClass('pagination');
			$('a', e).live('click.paginator', function (event) {
				if ($(this).attr('class') == 'prev') {
					// previous clicked
					o._set -= (o._set > 1) ? 1 : 0;
					self._update();
					return false;
				}
				else if ($(this).attr('class') == 'next') {
					// next clicked
					o._set += (o._set < o._maxsets) ? 1 : 0;
					self._update();
					return false;
				}
				else if ($(this).attr('class') == 'first') {
					// first clicked
					o._set = 1;
					self._update();
					return false;
				}
				else if ($(this).attr('class') == 'last') {
					// last clicked
					o._set = o._maxsets;
					self._update();
					return false;
				}
				else {
					// page link clicked
					o.currentPage = $(this).attr('id');
					self._update();
					e.trigger('paginate', o.currentPage);
					return false;
				}
			});
    		this._update();
    	},
    	destroy: function() {
			$('a', this.element).die('click.paginator');
			$(this.element).empty();
    		$.Widget.prototype.destroy.apply(this, arguments);
    	},
		refresh: function () {
			this._update();
		},
		_update: function () {
			var o = this.options, e = this.element;
			e.empty();
			
			typeof(o._set) !== 'undefined' || (o._set = Math.ceil(o.currentPage/10));
			o._maxsets = Math.ceil(o.pages/10);
			o._stop = Math.min(o.pages, (o._set * 10));
			
			if ((o._stop - 10) > 0) {
				o._start = Math.min(o._stop - 9, ((o._set-1)*10) + 1);
			} else {
				o._start = ((o._set-1)*10) + 1;
			}
			
			if (o._set > 1 && o.pages > 10) {
				e.append('<a href="javascript:;" class="first">&laquo;</a>');
				e.append('<a href="javascript:;" class="prev">...</a>');
			}
			
    		for (var i = o._start; i <= o._stop; i += 1) {
				if (i == o.currentPage) {
					e.append('<a href="javascript:;" id="'+i+'" class="current">'+i+'</a>');
				} else {
					e.append('<a href="javascript:;" id="'+i+'">'+i+'</a>');
				}
    		}

			if (o._set < o._maxsets && o.pages > 10) {
				e.append('<a href="javascript:;" class="next">...</a>');
				e.append('<a href="javascript:;" class="last">&raquo;</a>');
			}
		}
    });
    
    jQuery.fn.extend({
        maxlength: function(maxChars) {
            $(this).after("<div class='msg_counter'>-</div>");

            $(this).live('keyup', function() {
                var charLen = $(this).val().length;
                if (charLen > maxChars) {
                    $(this).val($(this).val().substring(0, maxChars));
                }
                if (charLen <= 457) msgParts = 3;
                if (charLen <= 305) msgParts = 2;
                if (charLen <= 160) msgParts = 1;
                $('div.msg_counter').html('<strong>' + charLen + '</strong> characters <strong>' + msgParts + '</strong> message parts');
            });
        },
    });
});