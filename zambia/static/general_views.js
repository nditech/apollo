// Backbone.js views
ContactEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "autocompleteChanged");
	},
	
	events: {
        "change input.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change #search_location": "autocompleteChanged",
        "submit": "save"
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = field.val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    autocompleteChanged: function (e) {
        var field = $(e.currentTarget);
        var data = {};
        match = /^search_(.*)/.exec(field.attr('id'));
		if (match) {
		    if (field.val()) {
		        data[match[1]] = field.val();
		    } else {
		        data[match[1]] = this.model.previous(match[1]);
		    }
			this.model.attributes[match[1]] = data[match[1]];
		}
    },
    		
	save: function () {
	    var self = this;
	    self.model.attributes.connections.models[0].save(false, {success: function () {
	        self.model.save(false, {success: function () {
    	        history.go(-1);
    	    }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
		$(self.el).html(Templates.ContactEdit(this.model.attributes));
		
		// Initialize values for drop down selections
		$('#partner', self.el).val(self.model.get('partner'));
		$('#role', self.el).val(self.model.get('role').get('resource_uri'));
		$('#gender', self.el).val(self.model.get('gender'));
		$('#cell_coverage', self.el).val(self.model.get('cell_coverage'));
		
		// Autocomplete for location input textbox
        $("#location", self.el).catcomplete({
            source: '/api/v1/location/search/',
            position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
            focus: function (event, ui) {
                $('#location').val(ui.item.name);
                return false;
            },
            select: function (event, ui) {
                $('#search_location').val(ui.item.resource_uri);
                $('#location').val(ui.item.name);
                $('#search_location').change();
                
                return false;
            }
        });

        $("#location", self.el).blur(function () {
            if (!$(this).val()) {
                $('#search_location', self.el).val("");
            }
            $('#search_location').change();
        });
        
		return self.el;
	}
});

ContactAddView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "autocompleteChanged");
	},
	
	events: {
        "change input.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change #search_location": "autocompleteChanged",
        "submit": "save"
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = field.val() || null;
        eval('this.model.attributes.'+field.attr('id')+' = value');
    },
    
    autocompleteChanged: function (e) {
        var field = $(e.currentTarget);
        var data = {};
        match = /^search_(.*)/.exec(field.attr('id'));
		if (match) {
		    if (field.val()) {
		        data[match[1]] = field.val();
		    } else {
		        data[match[1]] = this.model.previous(match[1]);
		    }
			this.model.attributes[match[1]] = data[match[1]];
		}
    },
    		
	save: function () {
	    var self = this;
	    self.model.save(false, {success: function () {
	        conn = new Connection();
            conn.attributes.backend = '/api/v1/backend/1/';
            conn.attributes.identity = $('#identity', self.el).val();
            conn.attributes.contact = self.model.get('resource_uri');

            conn.save(false, {success: function () {
                setTimeout(function () { history.go(-1); }, 200);
            }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
		$(self.el).html(Templates.ContactAdd());
		
		// Autocomplete for location input textbox
        $("#location", self.el).catcomplete({
            source: '/api/v1/location/search/',
            position: { my: 'left top', at: 'left bottom', collision: 'none', offset: '0 -4'},
            focus: function (event, ui) {
                $('#location').val(ui.item.name);
                return false;
            },
            select: function (event, ui) {
                $('#search_location').val(ui.item.resource_uri);
                $('#location').val(ui.item.name);
                $('#search_location').change();
                
                return false;
            }
        });

        $("#location", self.el).blur(function () {
            if (!$(this).val()) {
                $('#search_location', self.el).val("");
            }
            $('#search_location').change();
        });
        
		return self.el;
	}
});

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

ChecklistEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged", "locationChanged");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change .location_select": "locationChanged",
        "radio_click input:radio.field": "radioChanged",
        "submit": "save"
    },
    
    locationChanged: function (e) {
        var el = $(e.currentTarget);
        var location_type = $(el).attr("title");
        var id = $('option:selected', el).attr('title');
        
        if (id) {
            if (location_type == 'province') {
                $('.location_select').not(el).attr('disabled', 'disabled');
                $('.location_select').not(el).html('');
                
                var districts = new LocationCollection();
                districts.filtrate({'type__name': 'District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'district') {
                $('.location_select').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="province"]').not(el).html('');
                
                var constituencies = new LocationCollection();
                constituencies.filtrate({'type__name': 'Constituency', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="constituency"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'constituency') {
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var wards = new LocationCollection();
                wards.filtrate({'type__name': 'Ward', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="ward"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'ward') {
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var polling_districts = new LocationCollection();
                polling_districts.filtrate({'type__name': 'Polling District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'polling_district') {
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');

                var polling_streams = new LocationCollection();
                polling_streams.filtrate({'type__name': 'Polling Stream', 'parent__parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_stream"]').removeAttr('disabled');
                    }
                });
            }
        }   
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = ((field.val() == 0 && field.val() != "") || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
        self.model.get('response').save(false, {success: function () {
            self.model.save(false, {success: function () {
                setTimeout(function () { history.go(-1); }, 200);
            }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.ChecklistSectionTabs());
		//$(self.el).append(Templates.ChecklistMetadata(this.model.attributes));
		$(self.el).append(Templates.ChecklistEdit(this.model.attributes));
		$('div.pane:last', self.el).after(Templates.ChecklistSectionTabs());
		
		// Initialize values for drop down selections
		_(self.model.get('response').attributes).each(function (value, key) {
		    input_el = $('input[name="response.attributes.'+key+'"]:first', self.el);
		    		    
		    if ($(input_el).attr('type') == 'radio') {
		        $('input[name="response.attributes.'+key+'"][value="'+value+'"]', self.el).attr('checked', 'checked');
		    } else {
		        $('input[name="response.attributes.'+key+'"]', self.el).val(value);
		    }
		});
		
		$("input[name='response.attributes.J']", self.el).trigger('keyup');
        
        var provinces = new LocationCollection();
        provinces.filtrate({'type__name':'Province'}, {
           success: function (coll, response) {
               $('select[title="province"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}));
               var districts = new LocationCollection();
               districts.filtrate({'type__name':'District', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                   success: function (coll, response) {
                       $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}));
                       var constituencies = new LocationCollection();
                       constituencies.filtrate({'type__name':'Constituency', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                           success: function (coll, response) {
                               $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('id')}))
                               var wards = new LocationCollection();
                               wards.filtrate({'type__name':'Ward', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                                   success: function (coll, response) {
                                       $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('id')}));
                                       var polling_districts = new LocationCollection();
                                       polling_districts.filtrate({'type__name':'Polling District', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('id')}, {
                                           success: function (coll, response) {
                                               $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('id')}));
                                               var polling_streams = new LocationCollection();
                                               polling_streams.filtrate({'type__name':'Polling Stream', 'parent__parent__id':self.model.get('location').get('parent').get('parent').get('id')}, {
                                                   success: function (coll, response) {
                                                       $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('id')}));
                                                   }
                                               });
                                           }
                                       });
                                   }
                               });
                           }
                       });
                   }
               });
           }
        });
        
		return self.el;
	}
});

ChecklistAddView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged", "locationChanged");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change select.field": "selectionChanged",
        "change .location_select": "locationChanged",
        "radio_click input:radio.field": "radioChanged",
        "submit": "save"
    },
    
    locationChanged: function (e) {
        var el = $(e.currentTarget);
        var location_type = $(el).attr("title");
        var id = $('option:selected', el).attr('title');
        
        if (id) {
            if (location_type == 'province') {
                $('.location_select').not(el).attr('disabled', 'disabled');
                $('.location_select').not(el).html('');
                
                var districts = new LocationCollection();
                districts.filtrate({'type__name': 'District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'district') {
                $('.location_select').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="province"]').not(el).html('');
                
                var constituencies = new LocationCollection();
                constituencies.filtrate({'type__name': 'Constituency', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="constituency"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'constituency') {
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var wards = new LocationCollection();
                wards.filtrate({'type__name': 'Ward', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="ward"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'ward') {
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var polling_districts = new LocationCollection();
                polling_districts.filtrate({'type__name': 'Polling District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'polling_district') {
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');

                var polling_streams = new LocationCollection();
                polling_streams.filtrate({'type__name': 'Polling Stream', 'parent__parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_stream"]').removeAttr('disabled');
                    }
                });
            }
        }   
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = ((field.val() == 0 && field.val() != "") || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
	    // save the values for the response elsewhere so it doesn't affect object creation on the server
	    var response = self.model.get('response');
	    self.model.attributes.form = '/api/v1/checklist_form/1/';
	    
	    // save the checklist
        self.model.save(false, {success: function () {
            _(response.attributes).each(function (value, key) {
                self.model.get('response').attributes[key] = value;
            });
            self.model.attributes.response.save(false, {success: function () {
                setTimeout(function () { history.go(-1); }, 200);
            }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.ChecklistSectionTabs());
		$(self.el).append(Templates.ChecklistEdit());
		$('div.pane:last', self.el).after(Templates.ChecklistSectionTabs());
		        
        var provinces = new LocationCollection();
        provinces.filtrate({'type__name':'Province'}, {
           success: function (coll, response) {
               $('select[title="province"]').html(Templates.LocationOptions({'locations':coll.models}));
           }
        });
        
		return self.el;
	}
});


IncidentView = Backbone.View.extend({
	tagName: 'tr',
	
	initialize: function () {
		_.bindAll(this, "render");
		this.model.bind('change', this.render);
	},
	
	render: function () {
		$(this.el).html(Templates.Incident(this.model.attributes));
		return this.el;
	}
});

IncidentEditView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged", "locationChanged");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change input:hidden.field": "fieldChanged",
        "change textarea.field": "fieldChanged",
        "change .location_select": "locationChanged",
        "change select.field": "selectionChanged",
        "change input:checkbox.field": "radioChanged",
        "radio_click input:radio.field": "radioChanged", // a custom event is monitored to prevent out of order execution
        "submit": "save"
    },
        
    locationChanged: function (e) {
        var el = $(e.currentTarget);
        var location_type = $(el).attr("title");
        var id = $('option:selected', el).attr('title');
        
        if (id) {
            if (location_type == 'province') {
                $('.location_select').not(el).attr('disabled', 'disabled');
                $('.location_select').not(el).html('');
                
                var districts = new LocationCollection();
                districts.filtrate({'type__name': 'District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'district') {
                $('.location_select').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="province"]').not(el).html('');
                
                var constituencies = new LocationCollection();
                constituencies.filtrate({'type__name': 'Constituency', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="constituency"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'constituency') {
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var wards = new LocationCollection();
                wards.filtrate({'type__name': 'Ward', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="ward"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'ward') {
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var polling_districts = new LocationCollection();
                polling_districts.filtrate({'type__name': 'Polling District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'polling_district') {
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');

                var polling_streams = new LocationCollection();
                polling_streams.filtrate({'type__name': 'Polling Stream', 'parent__parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_stream"]').removeAttr('disabled');
                    }
                });
            }  
        }
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = (field.val() == 0 || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
      self.model.get('response').save(false, {success: function () {
        self.model.save(false, {success: function () {
	        setTimeout(function () { history.go(-1); }, 200);
	      }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.IncidentMetadata(this.model.attributes));
		$(self.el).append(Templates.IncidentEdit(this.model.attributes));
		
		// Initialize values for drop down selections
		_(self.model.get('response').attributes).each(function (value, key) {
		    input_el = $('input[name="response.attributes.'+key+'"]:first', self.el);
		    		    
		    if ($(input_el).attr('type') == 'radio') {
		        $('input[name="response.attributes.'+key+'"][value="'+value+'"]', self.el).attr('checked', 'checked');
		    } else if ($(input_el).attr('type') == 'checkbox') {
		        if (value) {
		            $('input[name="response.attributes.'+key+'"]', self.el).attr('checked', 'checked');
		        }
		    } else {
		        $('input[name="response.attributes.'+key+'"]', self.el).val(value);
		    }
		});
		$('textarea[name="response.attributes.description"]', self.el).val(self.model.get('response').get('description'));
				
        var provinces = new LocationCollection();
        provinces.filtrate({'type__name':'Province'}, {
           success: function (coll, response) {
               $('select[title="province"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}));
               var districts = new LocationCollection();
               districts.filtrate({'type__name':'District', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                   success: function (coll, response) {
                       $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}));
                       var constituencies = new LocationCollection();
                       constituencies.filtrate({'type__name':'Constituency', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                           success: function (coll, response) {
                               $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('id')}))
                               var wards = new LocationCollection();
                               wards.filtrate({'type__name':'Ward', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('parent').get('id')}, {
                                   success: function (coll, response) {
                                       $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('parent').get('id')}));
                                       var polling_districts = new LocationCollection();
                                       polling_districts.filtrate({'type__name':'Polling District', 'parent__id':self.model.get('location').get('parent').get('parent').get('parent').get('id')}, {
                                           success: function (coll, response) {
                                               $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('parent').get('parent').get('id')}));
                                               var polling_streams = new LocationCollection();
                                               polling_streams.filtrate({'type__name':'Polling Stream', 'parent__parent__id':self.model.get('location').get('parent').get('parent').get('id')}, {
                                                   success: function (coll, response) {
                                                       $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models, 'selected_id': self.model.get('location').get('id')}));
                                                   }
                                               });
                                           }
                                       });
                                   }
                               });
                           }
                       });
                   }
               });
           }
        });
        
		return self.el;
	}
});

IncidentAddView = Backbone.View.extend({
	tagName: 'div',
	
	initialize: function () {
		_.bindAll(this, "render", "save", "fieldChanged", "selectionChanged", "radioChanged", "locationChanged");
	},
	
	events: {
        "change input:text.field": "fieldChanged",
        "change input:hidden.field": "fieldChanged",
        "change textarea.field": "fieldChanged",
        "change .location_select": "locationChanged",
        "change select.field": "selectionChanged",
        "change input:checkbox.field": "radioChanged",
        "radio_click input:radio.field": "radioChanged", // a custom event is monitored to prevent out of order execution
        "submit": "save"
    },
        
    locationChanged: function (e) {
        var el = $(e.currentTarget);
        var location_type = $(el).attr("title");
        var id = $('option:selected', el).attr('title');
        
        if (id) {
            if (location_type == 'province') {
                $('.location_select').not(el).attr('disabled', 'disabled');
                $('.location_select').not(el).html('');
                
                var districts = new LocationCollection();
                districts.filtrate({'type__name': 'District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'district') {
                $('.location_select').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="province"]').not(el).html('');
                
                var constituencies = new LocationCollection();
                constituencies.filtrate({'type__name': 'Constituency', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="constituency"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="constituency"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'constituency') {
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var wards = new LocationCollection();
                wards.filtrate({'type__name': 'Ward', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="ward"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="ward"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'ward') {
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');
                
                var polling_districts = new LocationCollection();
                polling_districts.filtrate({'type__name': 'Polling District', 'parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_district"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_district"]').removeAttr('disabled');
                    }
                });
            } else if (location_type == 'polling_district') {
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).attr('disabled', 'disabled');
                $('.location_select').not('select[title="ward"]').not('select[title="constituency"]').not('select[title="district"]').not('select[title="province"]').not(el).html('');

                var polling_streams = new LocationCollection();
                polling_streams.filtrate({'type__name': 'Polling Stream', 'parent__parent__id': id}, {
                    success: function (coll, response) {
                        $('select[title="polling_stream"]').html(Templates.LocationOptions({'locations':coll.models}));
                        $('select[title="polling_stream"]').removeAttr('disabled');
                    }
                });
            }
        }   
    },
    
    radioChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $('input[name="'+field.attr('name')+'"]:checked').val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    selectionChanged: function (e) {
        var field = $(e.currentTarget);
        var value = $("option:selected", field).val() || null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    
    fieldChanged: function (e) {
        var field = $(e.currentTarget);
        var value = (field.val() == 0 || field.val()) ? field.val() : null;
        eval('this.model.attributes.'+field.attr('name')+' = value');
    },
    		
	save: function () {
	    var self = this;
	    // save the values for the response elsewhere so it doesn't affect object creation on the server
	    var response = self.model.get('response');
	    self.model.attributes.form = '/api/v1/incident_form/1/';
	    
	    // save the incident
        self.model.save(false, {success: function () {
            _(response.attributes).each(function (value, key) {
                self.model.get('response').attributes[key] = value;
            });
            self.model.attributes.response.save(false, {success: function () {
                setTimeout(function () { history.go(-1); }, 200);
            }});
	    }});
	    return false;
	},
	
	render: function () {
	    var self = this;
	    var input_el;
	    
		$(self.el).html(Templates.IncidentMetadata());
		$(self.el).append(Templates.IncidentEdit());
		
		$('.location_select', self.el).attr('disabled', 'disabled');
		
		provinces = new LocationCollection();
        provinces.filtrate({'type__name':'Province'}, {
           success: function (coll, response) {
               $('select[title="province"]', self.el).html(Templates.LocationOptions({'locations':coll.models})).removeAttr('disabled');
           }
        });
        
		return self.el;
	}
});