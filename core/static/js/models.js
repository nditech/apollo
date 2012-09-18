var LocationTypeModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/locationtypes'
});

var LocationModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/locations',

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
	}
	]
});

var PartnerModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/partners'
});

var FormModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/forms'
});

var FormGroupModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/formgroups'
});

var ObserverRoleModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/roles'
});

var ContactModel = Backbone.RelationalModel.extend({
	urlRoot: '/api/v1/contacts',

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