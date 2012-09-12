import re
from django.db import models


class Form(models.Model):
    name = models.CharField(max_length=255)
    trigger = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name

    def match(self, text):
        if re.match(self.trigger, text, re.I):
            return True

    @staticmethod
    def parse(text):
        forms = Form.objects.all()
        submission = {}

        # iterate over all forms, until we get a match
        for form in forms:
            if form.match(text):
                # begin submission processing
                submission['form_id'] = form.pk

                for group in form.groups.all():
                    for field in group.fields.all():
                        text = field.parse(text)
                        submission[field.tag.upper()] = field.value
                break
        else:
            raise Form.DoesNotExist
        return (submission, text)


class FormGroup(models.Model):
    name = models.CharField(max_length=32, blank=True)
    form = models.ForeignKey(Form, related_name='groups')

    class Meta:
        order_with_respect_to = 'form'


class FormField(models.Model):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(FormGroup, related_name='fields')
    tag = models.CharField(max_length=8)
    upper_limit = models.IntegerField(null=True)
    lower_limit = models.IntegerField(null=True)
    present_true = models.BooleanField(default=False)
    value = None

    class Meta:
        order_with_respect_to = 'group'

    def parse(self, text):
        pattern = r'{0}(?P<tagged>\d*)'.format(self.tag)

        match = re.search(pattern, text, re.I)

        if match:
            tagged = match.group('tagged')

            if tagged:
                self.value = int(tagged)
            elif self.present_true:
                # a value of 1 indicates presence/truth
                self.value = 1

        return re.sub(pattern, '', text, re.I) if self.value else text
