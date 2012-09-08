import re
from django.db import models


class ExtensibleForm(models.Model):
    name = models.CharField(max_length=32)
    trigger = models.CharField(max_length=32, unique=True)

    def __unicode__(self):
        return self.name

    # defined as a method so implementation can be overridden without
    # plenty of trouble
    def match(self, text):
        if self.trigger.lower() in text.lower():
            return True

    @staticmethod
    def parse(text):
        forms = ExtensibleForm.objects.all()
        submission = {}
        text_buffer = text.lower()

        # iterate over all forms, until we get a match
        for form in forms:
            if form.match(text):
                # begin submission processing
                text_buffer = text_buffer.replace(form.trigger.lower(), '')
                submission['form_id'] = form.pk

                for group in form.groups.all():
                    for field in group.fields.all():
                        text_buffer = field.parse(text_buffer)
                        submission[field.tag] = field.value
                break

        return (submission, text_buffer)


class FormGroup(models.Model):
    name = models.CharField(max_length=32, blank=True)
    form = models.ForeignKey(ExtensibleForm, related_name='groups')


class FormField(models.Model):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(FormGroup, related_name='fields')
    tag = models.CharField(max_length=8)
    upper_limit = models.IntegerField(null=True)
    lower_limit = models.IntegerField(null=True)
    present_true = models.BooleanField(default=False)
    value = None

    def parse(self, text):
        pattern = r'{0}(?P<tagged>\d?)'.format(self.tag)

        match = re.search(pattern, text, re.I)

        if match:
            tagged = match.group('tagged')

            if tagged:
                self.value = int(tagged)
            elif self.present_true:
                # a value of 1 indicates presence/truth
                self.value = 1

        subtext = self.tag.lower()
        if self.value:
            subtext = subtext + str(self.value)

        return text.lower().replace(subtext, '')
