from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from core.models import Form, FormGroup, FormField, FormFieldOption
from formbuilder.forms import FormForm, FormGroupForm, FormFieldForm, FormFieldOptionForm

# -- Forms --
class FormsListView(ListView):

	model = Form
	template_name = 'formbuilder/form_list.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(FormsListView, self).dispatch(request, *args, **kwargs)


class FormsCreateView(CreateView):

	model = Form
	form_class = FormForm
	template_name = 'formbuilder/form_create.html'
	success_url = reverse_lazy('forms-list')

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(FormsCreateView, self).dispatch(request, *args, **kwargs)


class FormsUpdateView(UpdateView):

	model = Form
	form_class = FormForm
	template_name = 'formbuilder/form_create.html'
	context_object_name = 'object'
	success_url = reverse_lazy('forms-list')

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(FormsUpdateView, self).dispatch(request, *args, **kwargs)

class FormsDetailView(DetailView):

	model = Form
	template_name = 'formbuilder/form_detail.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(FormsDetailView, self).dispatch(request, *args, **kwargs)


class FormsDeleteView(DeleteView):
	
	model = Form
	template_name = 'formbuilder/form_delete.html'
	success_url = reverse_lazy('forms-list')

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(FormsDeleteView, self).dispatch(request, *args, **kwargs)


# -- Form Groups --
class FormGroupsCreateView(CreateView):
	
	model = FormGroup
	form_class = FormGroupForm
	template_name = 'formbuilder/formgroup_create.html'
	context_object_name = 'object'

	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		return super(FormGroupsCreateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'form': self.form}

	def get_context_data(self, **kwargs):
		context = super(FormGroupsCreateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		return context


class FormGroupsUpdateView(UpdateView):
	
	model = FormGroup
	form_class = FormGroupForm
	template_name = 'formbuilder/formgroup_create.html'
	context_object_name = 'object'

	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		return super(FormGroupsUpdateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'form': self.form}

	def get_context_data(self, **kwargs):
		context = super(FormGroupsUpdateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		return context


class FormGroupsDeleteView(DeleteView):
	
	model = FormGroup
	template_name = 'formbuilder/formgroup_delete.html'
	
	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		return super(FormGroupsDeleteView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(FormGroupsDeleteView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		return context


# -- Form Field --
class FormFieldsCreateView(CreateView):
	
	model = FormField
	form_class = FormFieldForm
	template_name = 'formbuilder/formfield_create.html'
	
	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		self.formgroup = get_object_or_404(FormGroup, pk=kwargs['group_pk'])
		return super(FormFieldsCreateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'group': self.formgroup}

	def get_context_data(self, **kwargs):
		context = super(FormFieldsCreateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		context['formgroup_object'] = self.formgroup
		return context



class FormFieldsUpdateView(UpdateView):
	
	model = FormField
	form_class = FormFieldForm
	template_name = 'formbuilder/formfield_create.html'
	
	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		self.formgroup = get_object_or_404(FormGroup, pk=kwargs['group_pk'])
		return super(FormFieldsUpdateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'group': self.formgroup}

	def get_context_data(self, **kwargs):
		context = super(FormFieldsUpdateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		context['formgroup_object'] = self.formgroup
		return context


class FormFieldsDeleteView(DeleteView):
	
	model = FormField
	template_name = 'formbuilder/formfield_delete.html'
	
	def get_success_url(self):
		return reverse_lazy('form-detail', args=[self.form.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		return super(FormFieldsDeleteView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(FormFieldsDeleteView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		return context


# -- Form Field Option --
class FormFieldOptionsCreateView(CreateView):

	model = FormFieldOption
	form_class = FormFieldOptionForm
	template_name = 'formbuilder/formfieldoption_create.html'
	
	def get_success_url(self):
		return reverse_lazy('formfield-update', args=[self.form.pk, self.formgroup.pk, self.formfield.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		self.formgroup = get_object_or_404(FormGroup, pk=kwargs['group_pk'])
		self.formfield = get_object_or_404(FormField, pk=kwargs['field_pk'])
		return super(FormFieldOptionsCreateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'field': self.formfield}

	def get_context_data(self, **kwargs):
		context = super(FormFieldOptionsCreateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		context['formgroup_object'] = self.formgroup
		context['formfield_object'] = self.formfield
		return context


class FormFieldOptionsUpdateView(UpdateView):

	model = FormFieldOption
	form_class = FormFieldOptionForm
	template_name = 'formbuilder/formfieldoption_create.html'
	
	def get_success_url(self):
		return reverse_lazy('formfield-update', args=[self.form.pk, self.formgroup.pk, self.formfield.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		self.formgroup = get_object_or_404(FormGroup, pk=kwargs['group_pk'])
		self.formfield = get_object_or_404(FormField, pk=kwargs['field_pk'])
		return super(FormFieldOptionsUpdateView, self).dispatch(request, *args, **kwargs)

	def get_initial(self):
		return {'field': self.formfield}

	def get_context_data(self, **kwargs):
		context = super(FormFieldOptionsUpdateView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		context['formgroup_object'] = self.formgroup
		context['formfield_object'] = self.formfield
		return context


class FormFieldOptionsDeleteView(DeleteView):

	model = FormFieldOption
	template_name = 'formbuilder/formfieldoption_delete.html'
	
	def get_success_url(self):
		return reverse_lazy('formfield-update', args=[self.form.pk, self.formgroup.pk, self.formfield.pk])

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.form = get_object_or_404(Form, pk=kwargs['form_pk'])
		self.formgroup = get_object_or_404(FormGroup, pk=kwargs['group_pk'])
		self.formfield = get_object_or_404(FormField, pk=kwargs['field_pk'])
		return super(FormFieldOptionsDeleteView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(FormFieldOptionsDeleteView, self).get_context_data(**kwargs)
		context['form_object'] = self.form
		context['formgroup_object'] = self.formgroup
		context['formfield_object'] = self.formfield
		return context
