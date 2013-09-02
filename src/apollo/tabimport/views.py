import os

from django.conf import settings
from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from . import FileFactory


class DataImportView(SessionWizardView):
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'data'))

    def get_template_names(self):
        return ('tabimport/import.html',)

    def get_form_kwargs(self, step):
        if step == '1':
            data = self.get_cleaned_data_for_step('0')
            imp_file = FileFactory(data['upload'])
            return {'imp_file': imp_file, 'ct_id': data['model']}
        return super(DataImportView, self).get_form_kwargs(step)

    def done(self, form_list, **kwargs):
        try:
            created, modified = form_list[-1].import_data()
        except Exception as e:
            if settings.DEBUG:
                raise
            messages.error(self.request, _("The import failed. Error message: %s") % e)
        else:
            messages.info(self.request, _("Created objects: %(cr)d, modified objects: %(mod)d") % {
                'cr': created, 'mod': modified})
        self.file_storage.delete(self.get_cleaned_data_for_step('0')['upload'].file)
        return HttpResponseRedirect(reverse('admin:index'))
