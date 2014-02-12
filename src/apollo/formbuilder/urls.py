from django.conf.urls import patterns, url, include
from formbuilder.views import FormsListView, FormsDetailView, FormsDeleteView, FormsCreateView, FormsUpdateView
from formbuilder.views import FormGroupsCreateView, FormGroupsUpdateView, FormGroupsDeleteView
from formbuilder.views import FormFieldsCreateView, FormFieldsUpdateView, FormFieldsDeleteView
from formbuilder.views import FormFieldOptionsCreateView, FormFieldOptionsUpdateView, FormFieldOptionsDeleteView


urlpatterns = patterns('',
	# Form
	url(r'forms/?$', FormsListView.as_view(), name='forms-list'),
	url(r'forms/new$', FormsCreateView.as_view(), name='form-create'),
	url(r'form/(?P<pk>\d+)?$', FormsUpdateView.as_view(), name='form-update'),
	url(r'forms/(?P<pk>\d+)$', FormsDetailView.as_view(), name='form-detail'),
	url(r'form/(?P<pk>\d+)/delete$', FormsDeleteView.as_view(), name='form-delete'),

	# FormGroup
	url(r'form/(?P<form_pk>\d+)/group$', FormGroupsCreateView.as_view(), name='formgroup-create'),
	url(r'form/(?P<form_pk>\d+)/group/(?P<pk>\d+)$', FormGroupsUpdateView.as_view(), name='formgroup-update'),
	url(r'form/(?P<form_pk>\d+)/group/(?P<pk>\d+)/delete$', FormGroupsDeleteView.as_view(), name='formgroup-delete'),

	# FormField
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/?$', FormFieldsCreateView.as_view(), name="formfield-create"),
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/(?P<pk>\d+)$', FormFieldsUpdateView.as_view(), name="formfield-update"),
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/(?P<pk>\d+)/delete$', FormFieldsDeleteView.as_view(), name="formfield-delete"),

	# FormFieldOption
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/(?P<field_pk>\d+)/option/?$', FormFieldOptionsCreateView.as_view(), name='formfieldoption-create'),
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/(?P<field_pk>\d+)/option/(?P<pk>\d+)$', FormFieldOptionsUpdateView.as_view(), name='formfieldoption-update'),
	url(r'form/(?P<form_pk>\d+)/group/(?P<group_pk>\d+)/field/(?P<field_pk>\d+)/option/(?P<pk>\d+)/delete$', FormFieldOptionsDeleteView.as_view(), name='formfieldoption-delete'),
)
