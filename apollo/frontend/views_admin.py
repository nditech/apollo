# -*- coding: utf-8 -*-
from datetime import datetime
from flask import flash, g, send_file, redirect, request, session
from flask_admin import (
    form, BaseView, expose)
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import InlineModelFormList
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.form import rules, fields
from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.template import macro
from flask_babelex import lazy_gettext as _
from flask_security import current_user, login_required, roles_required
from flask_security.utils import hash_password, url_for_security
from io import BytesIO
from jinja2 import contextfunction
import pytz
from slugify import slugify
from wtforms import PasswordField, SelectField, SelectMultipleField, validators
from zipfile import ZipFile, ZIP_DEFLATED

from apollo.core import admin, db
from apollo import models, services, settings
from apollo.constants import LANGUAGE_CHOICES
from apollo.deployments.serializers import EventArchiveSerializer
from apollo.locations.views_locations import (
    locations_builder, import_divisions, export_divisions,
    locations_list, location_edit, locations_import, locations_headers,
    finalize_location_set)
from apollo.participants.views_participants import (
    participant_list, participant_list_import, participant_headers,
    participant_edit)
from apollo.formsframework.views_forms import (
    forms_list, export_form, checklist_init, form_builder, new_form, edit_form,
    quality_controls, quality_control_delete, quality_control_edit,
    import_form_schema, survey_init)


app_time_zone = pytz.timezone(settings.TIMEZONE)
utc_time_zone = pytz.utc

excluded_perm_actions = ['view_forms', 'access_event']

DATETIME_FORMAT_SPEC = '%Y-%m-%d %H:%M:%S %Z'


class MultipleSelect2Field(fields.Select2Field):
    def iter_choices(self):
        if self.allow_blank:
            yield (u'__None', self.blank_text, self.data is None)

        for value in self.data:
            yield (value, value, True)

    def process_data(self, value):
        """This is called when you create the form with existing data."""
        if value is None:
            self.data = []
        else:
            try:
                self.data = [self.coerce(value) for value in value]
            except (ValueError, TypeError):
                self.data = []

    def process_formdata(self, valuelist):
        """Process posted data."""
        if not valuelist:
            return

        if valuelist[0] == '__None':
            self.data = []
        else:
            try:
                self.data = [self.coerce(value) for value in valuelist]
            except ValueError:
                raise ValueError()

    def pre_validate(self, form):
        pass


class BaseAdminView(ModelView):
    page_size = settings.PAGE_SIZE

    def is_accessible(self):
        '''For checking if the admin view is accessible.'''
        if current_user.is_anonymous:
            return False

        deployment = current_user.deployment
        role = models.Role.query.filter_by(
            deployment_id=deployment.id, name='admin').first()
        return current_user.has_role(role)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for_security('login', next=request.url))


class ExtraDataInlineFormAdmin(InlineFormAdmin):
    form_columns = ('id', 'name', 'label', 'visible_in_lists')
    column_labels = {
        'name': _('Name'),
        'label': _('Label'),
        'visible_in_lists': _('Visible In Lists'),
    }
    column_descriptions = {
        'label': _('The display label to use for this field.'),
        'name': _('Internal name to use for this attribute. Avoid using spaces in the name.'),  # noqa
        'visible_in_lists': _('Specifies whether to display this field on data lists or not.'),  # noqa
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.deployment = g.deployment
            model.resource_type = model.__mapper_args__['polymorphic_identity']
        model.name = slugify(model.name, separator="_")

    def on_model_delete(self, model):
        # if this model has a resource attached to it, delete it as well
        models.Resource.query.filter_by(uuid=model.uuid).delete()


class ExtraDataInlineFormList(InlineModelFormList):
    def __init__(self, frm, session, model, prop, inline_view, **kwargs):
        self.form = frm
        self.session = session
        self.model = model
        self.prop = prop
        self.inline_view = inline_view
        self._pk = 'id'

        form_opts = form.FormOpts(
            widget_args=getattr(inline_view, 'form_widget_args', None),
            form_rules=inline_view._form_rules)
        form_field = self.form_field_type(frm, self._pk, form_opts=form_opts)
        super(InlineModelFormList, self).__init__(form_field, **kwargs)


class LocationExtraDataModelConverter(InlineModelConverter):
    inline_field_list_type = ExtraDataInlineFormList

    def _calculate_mapping_key_pair(self, model, info):
        return (
            models.LocationSet.extra_fields.key,
            models.LocationDataField.location_set.key)


class ParticipantExtraDataModelConverter(InlineModelConverter):
    inline_field_list_type = ExtraDataInlineFormList

    def _calculate_mapping_key_pair(self, model, info):
        return (
            models.ParticipantSet.extra_fields.key,
            models.ParticipantDataField.participant_set.key)


class DeploymentAdminView(BaseAdminView):
    can_create = False
    can_delete = False
    can_edit = True
    column_list = ('name', 'hostnames')
    column_default_sort = [(models.Deployment.id, True)]
    column_labels = {
        'name': _('Name'), 'hostnames': _('Hostnames'),
        'allow_observer_submission_edit': _('Allow Observer Submission Edit'),
        'dashboard_full_locations': _('Dashboard Full Locations'),
        'enable_partial_response_for_messages': _('Enable Partial Response For Messages'),  # noqa
    }
    column_descriptions = {
        'allow_observer_submission_edit': _('Specifies whether to allow the editing of observer data.'),  # noqa
        'dashboard_full_locations': _('Specifies whether to show all locations at an administrative division on the dashboard.'),  # noqa
        'enable_partial_response_for_messages': _('Specifies whether to respond with an error when a partial response is received for a text message.'),  # noqa
        'hostnames': _('An example of a hostname is "example.com". Used internally to determine what deployment to access.'),  # noqa
    }
    form_edit_rules = [
        rules.FieldSet(
            (
                'name', 'allow_observer_submission_edit',
                'dashboard_full_locations',
                'enable_partial_response_for_messages', 'hostnames',
                'primary_locale', 'other_locales'
            ),
            _('Deployment')
        )
    ]
    form_overrides = {
        'hostnames': MultipleSelect2Field
    }
    form_args = {
        'hostnames': {
            'render_kw': {"multiple": "multiple", "data-role": "select2-tags"},
            'choices': []
        }
    }

    form_columns = ['name', 'hostnames', 'dashboard_full_locations',
                    'enable_partial_response_for_messages',
                    'allow_observer_submission_edit', 'primary_locale',
                    'other_locales']

    def _on_model_change(self, form, model, is_created):
        # strip out the empty strings
        if model.primary_locale == '':
            model.primary_locale = None
        model.other_locales = [loc for loc in model.other_locales if loc != '']

    def get_query(self):
        return models.Deployment.query.filter_by(
            id=current_user.deployment.id)

    def scaffold_form(self):
        form_class = super().scaffold_form()
        # not stripping the first item for the primary locale
        # because stripping it would mean the language is
        # set to the next item if nothing is selected and
        # the choice is saved. as at this moment, the next
        # item is the choice for Arabic
        form_class.primary_locale = SelectField(
            _('Primary Language'), choices=LANGUAGE_CHOICES,
            validators=[validators.optional()],
            description=_('Specifies the primary language that will be supported for data uploads.'))  # noqa
        # stripping the first item for the other locales
        # so that we avoid the "None is not a valid choice"
        # error when it is selected by mistake
        form_class.other_locales = SelectMultipleField(
            _('Other Languages'), choices=LANGUAGE_CHOICES,
            validators=[validators.optional()],
            description=_('Specifies other languages that will be supported for data uploads.'))  # noqa

        return form_class


class EventAdminView(BaseAdminView):
    column_filters = ('name', 'start', 'end')
    column_list = ('name', 'start', 'end', 'location_set', 'participant_set',
                   'archive')
    column_labels = {
        'name': _('Name'), 'start': _('Start'), 'end': _('End'),
        'location_set': _('Location Set'),
        'participant_set': _('Participant Set'), 'archive': _('Archive')}
    column_descriptions = {
        'start': _('What time the event is to start in the local time.'),
        'end': _('What time the event is to end in the local time.'),
        'forms': _('What forms should be enabled for this event.')
    }
    column_default_sort = [(models.Event.start, True)]
    form_columns = ('name', 'start', 'end', 'forms', 'participant_set')
    form_rules = [
        rules.FieldSet(
            ('name', 'start', 'end', 'forms', 'participant_set'),
            _('Event'))
    ]
    column_formatters = {
        'archive': macro('event_archive'),
    }

    @expose('/download/<int:event_id>')
    def download(self, event_id):
        event = services.events.find(id=event_id).first_or_404()
        eas = EventArchiveSerializer()

        fp = BytesIO()
        with ZipFile(fp, 'w', ZIP_DEFLATED) as zf:
            eas.serialize(event, zf)

        fp.seek(0)
        fname = slugify(
            f'event archive {event.name.lower()} {datetime.utcnow().strftime("%Y %m %d %H%M%S")}')  # noqa

        return send_file(
            fp,
            attachment_filename=f'{fname}.zip',
            as_attachment=True)

    def get_one(self, pk):
        event = super(EventAdminView, self).get_one(pk)

        # convert start and end dates to app time zone
        event.start = event.start.astimezone(app_time_zone)
        event.end = event.end.astimezone(app_time_zone)
        return event

    @contextfunction
    def get_list_value(self, context, model, name):
        if name in ['start', 'end']:
            attribute = getattr(model, name, None)
            if attribute:
                return attribute.astimezone(
                    app_time_zone).strftime(DATETIME_FORMAT_SPEC)

            return attribute

        return super(EventAdminView, self).get_list_value(context, model, name)

    def get_query(self):
        '''Returns the queryset of the objects to list.'''
        user = current_user._get_current_object()
        return models.Event.query.filter_by(deployment_id=user.deployment.id)

    def on_model_change(self, form, model, is_created):
        # if we're creating a new event, make sure to set the
        # deployment, since it won't appear in the form
        if is_created:
            model.deployment = current_user.deployment

            # add role permissions for this event
            roles = models.Role.query.filter_by(
                deployment=model.deployment).all()
            model.roles = roles

        if form.participant_set.data:
            model.location_set = form.participant_set.data.location_set
        else:
            model.location_set = None

        # convert to the app time zone
        model.start = app_time_zone.localize(
            model.start).astimezone(utc_time_zone)
        model.end = app_time_zone.localize(
            model.end).astimezone(utc_time_zone)


class UserAdminView(BaseAdminView):
    '''Thanks to mrjoes and this Flask-Admin issue:
    https://github.com/mrjoes/flask-admin/issues/173
    '''
    column_list = ('email', 'roles', 'active')
    column_labels = {'roles': _('Roles'), 'active': _('Active')}
    column_searchable_list = ('email',)
    column_descriptions = {
        'roles': _('What roles are assigned to this user.'),
        'permissions': _('Explicitly specifies which non-role permissions (in addition) to assign to the user.'),  # noqa
    }
    column_default_sort = [(models.User.email, False)]
    form_columns = (
        'email', 'username', 'active', 'roles', 'permissions', 'locale')
    form_excluded_columns = ('password', 'confirmed_at', 'login_count',
                             'last_login_ip', 'last_login_at',
                             'current_login_at', 'deployment',
                             'current_login_ip', 'submission_comments')
    form_rules = [
        rules.FieldSet(('email', 'username', 'password2', 'active', 'roles',
                        'permissions', 'locale'))
    ]

    def get_query(self):
        user = current_user._get_current_object()
        return models.User.query.filter_by(deployment=user.deployment)

    def on_model_change(self, form, model, is_created):
        if form.password2.data:
            model.password = hash_password(form.password2.data)
        if is_created:
            model.deployment = current_user.deployment
        if not form.locale.data:
            model.locale = None

    def create_form(self, obj=None):
        form = super().create_form(obj)

        deployment = current_user.deployment

        # local function helper
        def _get_deployment_roles():
            return models.Role.query.filter_by(deployment_id=deployment.id)

        form.roles.query_factory = _get_deployment_roles

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        deployment = current_user.deployment

        # local function helper
        def _get_deployment_roles():
            return models.Role.query.filter_by(deployment_id=deployment.id)

        form.roles.query_factory = _get_deployment_roles

        return form

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password2 = PasswordField(_('New Password'))
        form_class.locale = SelectField(
            _('Language'), choices=LANGUAGE_CHOICES,
            description=_("Specifies the user's default language."))
        return form_class

    @action('disable', _('Disable'),
            _('Are you sure you want to disable the selected users?'))
    def action_disable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = False
            role.save()
        flash(str(_('User(s) successfully disabled.')), 'success')

    @action('enable', _('Enable'),
            _('Are you sure you want to enable the selected users?'))
    def action_enable(self, ids):
        for role in models.User.query.filter(models.User.id.in_(ids)):
            role.active = True
            role.save()
        flash(str(_('User(s) successfully enabled.')), 'success')


class RoleAdminView(BaseAdminView):
    can_delete = False
    column_list = ('name', 'description')
    column_labels = {'name': _('Name'), 'description': _('Description')}
    column_descriptions = {
        'description': _('Optional description for the role.'),
        'permissions': _('Specifies which permissions to assign to users with this role.'),  # noqa
        'resources': _('Specifies which resources (e.g. forms) to allow users with this role to access.'),  # noqa
    }
    column_default_sort = [(models.Role.name, False)]
    form_columns = ('name', 'description', 'permissions', 'resources')

    def create_form(self, obj=None):
        deployment = g.deployment
        form = super().create_form(obj)
        form.resources.query = models.Resource.query.filter_by(
            deployment=deployment)

        return form

    def edit_form(self, obj=None):
        deployment = g.deployment
        form = super().edit_form(obj)
        form.resources.query = models.Resource.query.filter_by(
            deployment=deployment)

        return form

    def get_one(self, pk):
        deployment = current_user.deployment
        return models.Role.query.filter_by(
            deployment_id=deployment.id, id=pk).first_or_404()

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.deployment = current_user.deployment
        super().on_model_change(form, model, is_created)


class SetViewMixin(object):
    column_filters = ('name',)

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.deployment_id = current_user.deployment.id
        super().on_model_change(form, model, is_created)


class LocationSetAdminView(SetViewMixin, BaseAdminView):
    column_list = ('name', 'administrative_divisions', 'locations')
    column_labels = {
        'name': _('Name'),
        'administrative_divisions': _('Administrative Divisions'),
        'locations': _('Location Data')
    }
    column_formatters = {
        'administrative_divisions': macro('locations_builder'),
        'locations': macro('locations_list'),
    }
    column_default_sort = [(models.LocationSet.name, False)]
    form_columns = ('name',)
    inline_models = (ExtraDataInlineFormAdmin(models.LocationDataField),)
    inline_model_form_converter = LocationExtraDataModelConverter

    def on_model_delete(self, model):
        # delete dependent objects first
        models.LocationPath.query.filter_by(location_set=model).delete()
        models.Location.query.filter_by(location_set=model).delete()
        models.LocationTypePath.query.filter_by(location_set=model).delete()
        models.LocationType.query.filter_by(location_set=model).delete()
        return super().on_model_delete(model)

    @expose('/builder/<int:location_set_id>', methods=['GET', 'POST'])
    def builder(self, location_set_id):
        return locations_builder(self, location_set_id)

    @expose('/builder/<int:location_set_id>/import', methods=['POST'])
    def import_divisions(self, location_set_id):
        return import_divisions(location_set_id)

    @expose('/builder/<int:location_set_id>/export')
    def export_divisions(self, location_set_id):
        return export_divisions(location_set_id)

    @expose('/locations/<int:location_set_id>')
    def locations_list(self, location_set_id):
        return locations_list(self, location_set_id)

    @expose('/locations/<int:location_set_id>/import', methods=['POST'])
    def locations_import(self, location_set_id):
        return locations_import(location_set_id)

    @expose('/locations/<int:location_set_id>/finalize', methods=['POST'])
    def locations_finalize(self, location_set_id):
        return finalize_location_set(location_set_id)

    @expose(
        '/locations/<int:location_set_id>/headers/<int:upload_id>',
        methods=['GET', 'POST']
    )
    def locations_headers(self, location_set_id, upload_id):
        return locations_headers(self, location_set_id, upload_id)

    @expose('/location/<int:id>', methods=['GET', 'POST'])
    def location_edit(self, id):
        return location_edit(self, id)


class ParticipantSetAdminView(SetViewMixin, BaseAdminView):
    column_list = ('name', 'location_set', 'participants')
    column_labels = {
        'name': _('Name'),
        'location_set': _('Location Set'),
        'participants': _('Participants'),
        'gender_hidden': _('Hide Gender'),
        'role_hidden': _('Hide Role'),
        'partner_hidden': _('Hide Organization'),
    }
    column_descriptions = {
        'gender_hidden': _('If enabled, will hide the gender in the participant list.'),  # noqa
        'role_hidden': _('If enabled, will hide the role in the participant list.'),  # noqa
        'partner_hidden': _('If enabled, will hide the organization in the participant list.'),  # noqa
    }
    column_default_sort = [(models.ParticipantSet.name, False)]
    form_columns = (
        'name', 'location_set', 'gender_hidden', 'role_hidden',
        'partner_hidden')
    column_formatters = {
        'participants': macro('participants_list')
    }
    inline_models = (ExtraDataInlineFormAdmin(models.ParticipantDataField),)
    inline_model_form_converter = ParticipantExtraDataModelConverter

    def create_form(self, obj=None):
        deployment = g.deployment
        form = super().create_form(obj)
        form.location_set.choices = models.LocationSet.query.filter_by(
            deployment=deployment).with_entities(
                models.LocationSet.id, models.LocationSet.name).all()

        return form

    def edit_form(self, obj=None):
        deployment = g.deployment
        form = super().edit_form(obj)
        form.location_set.choices = models.LocationSet.query.filter_by(
            deployment=deployment).with_entities(
                models.LocationSet.id, models.LocationSet.name).all()

        return form

    def after_model_change(self, form, model, is_created):
        _role = models.ParticipantRole.query.filter(
            models.ParticipantRole.name == '$FC',
            models.ParticipantRole.participant_set == model).first()
        if not _role:
            _role = models.ParticipantRole.create(
                name='$FC', participant_set=model)

    @expose('/participants/<int:participant_set_id>', methods=['GET', 'POST'])
    def participants_list(self, participant_set_id):
        return participant_list(participant_set_id, self)

    @expose('/participants/<int:participant_set_id>/import', methods=['POST'])
    def participants_import(self, participant_set_id):
        return participant_list_import(participant_set_id)

    @expose(
        '/participants/<int:participant_set_id>/headers/<int:upload_id>',
        methods=['GET', 'POST']
    )
    def participants_headers(self, participant_set_id, upload_id):
        return participant_headers(upload_id, participant_set_id, self)

    @expose('/participant/<int:id>', methods=['GET', 'POST'])
    def participant_edit(self, id):
        return participant_edit(id, self)


class FormsView(BaseView):
    def is_accessible(self):
        '''For checking if the admin view is accessible.'''
        if current_user.is_anonymous:
            return False

        deployment = current_user.deployment
        role = models.Role.query.filter_by(
            deployment_id=deployment.id, name='admin').first()
        return current_user.has_role(role)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for_security('login', next=request.url))

    @expose('/')
    def index(self):
        return forms_list(self)

    @expose('/<int:form_id>/export')
    def form_export(self, form_id):
        return export_form(form_id)

    @expose('/new', methods=['GET', 'POST'])
    def create_form(self):
        return new_form(self)

    @expose('/<int:form_id>', methods=['GET', 'POST'])
    def edit_form(self, form_id):
        return edit_form(self, form_id)

    @expose('/import', methods=['POST'])
    def import_form(self):
        return import_form_schema()

    @expose('/builder/<int:form_id>', methods=['GET', 'POST'])
    def builder(self, form_id):
        return form_builder(self, form_id)

    @expose('/init', methods=['POST'])
    def init(self):
        return checklist_init()

    @expose('/survey_init', methods=['POST'])
    def init_surveys(self):
        return survey_init()

    @expose('/qa/<int:form_id>', methods=['GET'])
    def qc(self, form_id):
        return quality_controls(self, form_id)

    @expose('/qa/<int:form_id>/<string:qa>', methods=['GET', 'POST', 'DELETE'])
    def quality_control_edit(self, form_id, qa):
        if request.method == 'DELETE':
            return quality_control_delete(self, form_id, qa)
        else:
            return quality_control_edit(self, form_id, qa)

    @expose('/qa/<int:form_id>/new', methods=['GET', 'POST'])
    def quality_control_add(self, form_id):
        return quality_control_edit(self, form_id)


class TaskView(BaseView):
    @expose('/')
    @login_required
    @roles_required('admin')
    def index(self):
        context = {'channel': session.get('_id')}
        template_name = 'admin/tasks.html'

        return self.render(template_name, **context)


admin.add_view(DeploymentAdminView(models.Deployment, db.session))
admin.add_view(
    EventAdminView(models.Event, db.session, _('Events')))
admin.add_view(UserAdminView(models.User, db.session, _('Users')))
admin.add_view(RoleAdminView(models.Role, db.session, _('Roles')))
admin.add_view(
    LocationSetAdminView(models.LocationSet, db.session, _('Location Sets')))
admin.add_view(
    ParticipantSetAdminView(
        models.ParticipantSet, db.session, _('Participant Sets')))
admin.add_view(FormsView(name=_("Forms")))
admin.add_view(TaskView(name=_('Tasks')))
