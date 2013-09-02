from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from . import FileFactory, UnsupportedFileFormat


class FileuploadForm(forms.Form):
    upload = forms.FileField()
    model = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(FileuploadForm, self).__init__(*args, **kwargs)
        # Dynamically set model choices
        choices = []
        for ct in ContentType.objects.all():
            if getattr(ct.model_class(), 'support_tabimport', False):
                choices.append((ct.id, ct.name))
        self.fields['model'].choices = choices

    def clean_upload(self):
        f = self.cleaned_data['upload']
        try:
            imp_file = FileFactory(f)
        except UnsupportedFileFormat as e:
            raise forms.ValidationError("Error: %s" % e)
        return f


class MatchingForm(forms.Form):
    key = forms.ChoiceField(help_text=_(
        'The key field is the field which will determine if the entry is a new one. Typically a unique ID field.'))
    #FIXME: to be implemented
    #arch_staled = forms.BooleanField(label=_("Archive objects not in imported list"),
    #    initial=False, required=False)

    def __init__(self, imp_file, ct_id, *args, **kwargs):
        super(MatchingForm, self).__init__(*args, **kwargs)
        # Construct fields dynamically based on chosen model
        self.imp_file = imp_file
        self.model = ContentType.objects.get(pk=ct_id).model_class()
        choices = list((f.name, f.verbose_name) for f in self.model._meta.fields if not f.auto_created)
        choices.insert(0, ('', '--------'))
        for i, head in enumerate(self.imp_file.get_headers()):
            self.fields[str(i)] = forms.ChoiceField(choices=choices, required=False, label=head)
        self.fields['key'].choices = choices

    def import_data(self):
        def is_int(s):
            try: 
                int(s)
                return True
            except ValueError:
                return False

        headers = self.imp_file.get_headers()
        mapping = dict((val, headers[int(key)]) for key, val in self.cleaned_data.items() if is_int(key) and val != '')
        obj_created = obj_modified = 0
        for line in self.imp_file:
            defaults = dict((key, line[val]) for key, val in mapping.items() if key != self.cleaned_data['key'])
            if hasattr(self.model, 'prepare_import'):
                # Hook to let a chance to the model to handle special values
                defaults = self.model.prepare_import(defaults)
            key_mapping = {
                self.cleaned_data['key']: line[mapping[self.cleaned_data['key']]],
                'defaults': defaults
            }
            obj, created = self.model.objects.get_or_create(**key_mapping)
            if not created:
                for key, val in defaults.items():
                    setattr(obj, key, val)
                    obj.save()
                obj_modified += 1
            else:
                obj_created += 1
        #FIXME: implement arch_staled
        return obj_created, obj_modified
