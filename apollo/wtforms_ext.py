# from https://github.com/industrydive/wtforms_extended_selectfield
from wtforms.fields import SelectField, SelectMultipleField
from wtforms.validators import ValidationError
from wtforms.widgets import HTMLString, html_params
from wtforms.widgets import Select

# very loosely based on https://gist.github.com/playpauseandstop/1590178

__all__ = ('ExtendedSelectField', 'ExtendedSelectWidget')


class ExtendedSelectWidget(Select):
    """
    Add support of choices with ``optgroup`` to the ``Select`` widget.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for item1, item2 in field.choices:
            if isinstance(item2, (list, tuple)):
                group_label = item1
                group_items = item2
                html.append('<optgroup %s>' % html_params(label=group_label))
                for inner_val, inner_label in group_items:
                    if field.data:
                        html.append(self.render_option(inner_val, inner_label, inner_val in field.data))
                    else:
                        html.append(self.render_option(inner_val, inner_label, inner_val == field.data))
                html.append('</optgroup>')
            else:
                val = item1
                label = item2
                html.append(self.render_option(val, label, val == field.data))
        html.append('</select>')
        return HTMLString(''.join(html))


class ExtendedSelectField(SelectField):
    """
    Add support of ``optgroup`` grouping to default WTForms' ``SelectField`` class.

    Here is an example of how the data is laid out.

        (
            ('Fruits', (
                ('apple', 'Apple'),
                ('peach', 'Peach'),
                ('pear', 'Pear')
            )),
            ('Vegetables', (
                ('cucumber', 'Cucumber'),
                ('potato', 'Potato'),
                ('tomato', 'Tomato'),
            )),
            ('other','None Of The Above')
        )

    It's a little strange that the tuples are (value, label) except for groups which are (Group Label, list of tuples)
    but this is actually how Django does it too https://docs.djangoproject.com/en/dev/ref/models/fields/#choices

    """
    widget = ExtendedSelectWidget()

    def iter_choices(self):
        for value, label in self.choices:
            if isinstance(label, (list, tuple)):
                for inner_val, inner_label in label:
                    selected = self.data is not None and self.coerce(inner_val) in self.data
                    yield (inner_val, inner_label, selected)
            else:
                selected = self.data is not None and self.coerce(value) in self.data
                yield (value, label, selected)

    def pre_validate(self, form):
        """
        Don't forget to validate also values from embedded lists.
        """
        for item1, item2 in self.choices:
            if isinstance(item2, (list, tuple)):
                group_label = item1
                group_items = item2
                for val,label in group_items:
                    if val == self.data:
                        return
            else:
                val = item1
                label = item2
                if val == self.data:
                    return
        raise ValidationError(self.gettext('Not a valid choice!'))


class ExtendedMultipleSelectField(SelectMultipleField):
    widget = ExtendedSelectWidget(multiple=True)

    def iter_choices(self):
        for value, label in self.choices:
            if isinstance(label, (list, tuple)):
                for inner_val, inner_label in label:
                    selected = self.data is not None and self.coerce(inner_val) in self.data
                    yield (inner_val, inner_label, selected)
            else:
                selected = self.data is not None and self.coerce(value) in self.data
                yield (value, label, selected)

    def pre_validate(self, form):
        """
        Don't forget to validate also values from embedded lists.
        """
        if self.data:
            values = []
            for c in self.choices:
                if isinstance(c[1], (list, tuple)):
                    values.extend(i[0] for i in c[1])
                else:
                    values.append(c[0])
            for d in self.data:
                if d not in values:
                    raise ValueError(self.gettext("'%(value)s' is not a valid choice for this field") % dict(value=d))
