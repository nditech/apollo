from django import forms
from core.models import Form, FormGroup, FormField, FormFieldOption

class FormForm(forms.ModelForm):
	name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class':'form-control'}))
	type = forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}), choices=Form.FORM_TYPES)
	trigger = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class':'form-control'}))
	field_pattern = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class':'form-control'}), required=False)
	options = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), required=False)

	class Meta:
		model = Form


class FormGroupForm(forms.ModelForm):
	name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control'}))
	form = forms.ModelChoiceField(queryset=Form.objects.all(), widget=forms.HiddenInput)

	class Meta:
		model = FormGroup


class FormFieldForm(forms.ModelForm):
	name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control'}))
	tag = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class': 'form-control'}))
	description = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
	group = forms.ModelChoiceField(queryset=FormGroup.objects.all(), widget=forms.HiddenInput)
	lower_limit = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
	upper_limit = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
	analysis_type = forms.ChoiceField(widget=forms.Select(attrs={'class':'form-control'}), choices=FormField.ANALYSIS_TYPES)

	class Meta:
		model = FormField


class FormFieldOptionForm(forms.ModelForm):
	field = forms.ModelChoiceField(queryset=FormField.objects.all(), widget=forms.HiddenInput)
	description = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
	option = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'form-control'}))

	class Meta:
		model = FormFieldOption
