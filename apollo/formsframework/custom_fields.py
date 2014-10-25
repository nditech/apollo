import re
import wtforms

WTF_MAJOR_VERSION = int(wtforms.__version__[0])

if WTF_MAJOR_VERSION == 1:
    unset_value = wtforms.fields.core._unset_value
elif WTF_MAJOR_VERSION == 2:
    unset_value = wtforms.utils.unset_value


class IntegerSplitterField(wtforms.IntegerField):
    pattern = re.compile(r'\d{1}')
    widget = wtforms.widgets.Select(multiple=True)

    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super(wtforms.IntegerField, self).__init__(label, validators, **kwargs)
        self.choices = choices

    def process(self, formdata, data=unset_value):
        super(wtforms.IntegerField, self).process(formdata, data)

        temp = IntegerSplitterField.pattern.findall(unicode(self.data))
        self.data = list({int(i) for i in temp})

    def pre_validate(self, form):
        if self.data:
            values = list(c[0] for c in self.choices)
            for d in self.data:
                if d not in values:
                    raise ValueError(
                        self.gettext(
                            "'%(value)s' is not a valid choice for this field"
                        ) % dict(value=d))
