# -*- coding: utf-8 -*-
import re

import wtforms


class IntegerSplitterField(wtforms.IntegerField):
    pattern = re.compile(r"\d{1}")
    widget = wtforms.widgets.Select(multiple=True)

    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        """Initializer."""
        super(wtforms.IntegerField, self).__init__(label, validators, **kwargs)
        self.choices = choices

    def process(self, formdata, data=wtforms.utils.unset_value, **kwargs):
        super(wtforms.IntegerField, self).process(formdata, data)

        temp = IntegerSplitterField.pattern.findall(str(self.data))
        self.data = list({int(i) for i in temp})

    def pre_validate(self, form):
        if self.data:
            values = [c[0] for c in self.choices]
            for d in self.data:
                if d not in values:
                    raise ValueError(self.gettext("'%(value)s' is not a valid choice for this field") % {"value": d})
