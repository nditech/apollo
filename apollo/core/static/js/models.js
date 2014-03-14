var apiRoot = '/api/v1';


var MessageLogModel = Backbone.RelationalModel.extend({
	resourceName: 'messagelog',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var LocationTypeModel = Backbone.RelationalModel.extend({
	resourceName: 'locationtypes',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var LocationModel = Backbone.RelationalModel.extend({
	resourceName: 'locations',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	},

	relations: [{
		type: Backbone.HasOne,
		key: 'type',
		relatedModel: LocationTypeModel,
		reverseRelation: {
			// TODO: not quite sure we will use
			// the reverse relation
		}
	}, {
		type: Backbone.HasOne,
		key: 'parent',
		relatedModel: LocationModel,
		reverseRelation: {
			key: 'children'
		}
	}]
});

var PartnerModel = Backbone.RelationalModel.extend({
	resourceName: 'partners',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var FormModel = Backbone.RelationalModel.extend({
	resourceName: 'forms',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var FormGroupModel = Backbone.RelationalModel.extend({
	resourceName: 'formgroups',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var RoleModel = Backbone.RelationalModel.extend({
	resourceName: 'roles',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	}
});

var ContactModel = Backbone.RelationalModel.extend({
	resourceName: 'contacts',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	},

	relations: [{
		type: Backbone.HasOne,
		key: 'location',
		relatedModel: LocationModel
	}, {
		type: Backbone.HasOne,
		key: 'supervisor',
		relatedModel: ContactModel
	}, {
		type: Backbone.HasOne,
		key: 'role',
		relatedModel: ObserverRoleModel
	}, {
		type: Backbone.HasOne,
		key: 'partner',
		relatedModel: PartnerModel
	}]
});

var SubmissionModel = Backbone.RelationalModel.extend({
	resourceName: 'submissions',
	urlRoot: function() {
		return (apiRoot + '/' + this.resourceName);
	},

	relations: [{
		type: Backbone.HasOne,
		key: 'observer',
		relatedModel: ContactModel
	}, {
		type: Backbone.HasOne,
		key: 'form',
		relatedModel: FormModel
	}],

	// the default save method
	_defaultSave: function(key, value, options) {
		Backbone.RelationalModel.prototype.save.call(this, key, value, options);
	},

	// the overridden save method
	save: function(key, value, options) {
		// call the default setter
		this.set(key, value, options);

		// remove any invalid data in the data attribute
		var data = this.get('data');

		if (!_.isObject(data))
			// data is supposed to be a hash
			data = {};
		else {
			for (property in data) {
				var prop = data[property];
				var val = Number(prop);

				// from underscore's implementation of _.isNaN()!
				if (val !== val) {
					delete data[property];
					continue;
				}

				// nulls and empty strings are converted to 0 by Number
				if (prop == null)
					delete data[property];
			}
		}

		// revert to the default save
		this._defaultSave('data', data);
	}
});