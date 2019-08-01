# -*- coding: utf-8 -*-
from dateutil.parser import parse
from dateutil.tz import gettz, UTC
from flask_babelex import lazy_gettext as _
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from wtforms import Form as WTForm, fields

from apollo.core import CharFilter, ChoiceFilter, FilterSet
from apollo.formsframework.models import Form
from apollo.messaging.models import Message
from apollo.settings import TIMEZONE

InboundMessage = Message
OutboundMessage = aliased(Message)
APP_TZ = gettz(TIMEZONE)


def make_submission_type_field_choices():
    choices = [
        ('', _('Form Type')),
        ('Invalid', _('Invalid Form'))
    ]

    choices.extend(Form.FORM_TYPES)

    return choices


class MobileFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            query_val = f'%{value}%'
            return query.filter(
                or_(
                    Message.sender.ilike(query_val),
                    Message.recipient.ilike(query_val)
                )
            )

        return query


class TextFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            query_val = f'%{value}%'
            return query.filter(Message.text.ilike(query_val))

        return query


class DateFilter(CharFilter):
    def queryset_(self, query, value):
        if value:
            try:
                dt = parse(value, dayfirst=True)
            except (OverflowError, ValueError):
                return query.filter(False)

            dt = dt.replace(tzinfo=APP_TZ).astimezone(
                    UTC).replace(tzinfo=None)
            upper_bound = dt.replace(hour=23, minute=59, second=59)
            lower_bound = dt.replace(hour=0, minute=0, second=0)

            return query.filter(
                Message.received >= lower_bound,
                Message.received <= upper_bound
            )

        return query


class SubmissionFormTypeFilter(ChoiceFilter):
    field_class = fields.SelectField

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = make_submission_type_field_choices()

        super().__init__(*args, **kwargs)

    def queryset_(self, query, value):
        if value:
            if value == 'Invalid':
                return query.filter(Message.submission_id == None)  # noqa
            else:
                return query.filter(Form.form_type == value)

        return query


class MessageFilterSet(FilterSet):
    mobile = MobileFilter()
    text = TextFilter()
    date = DateFilter()
    form_type = SubmissionFormTypeFilter()


class MessageFilterForm(WTForm):
    mobile = fields.StringField()
    text = fields.StringField()
    date = fields.StringField()
    form_type = fields.SelectField(
        choices=make_submission_type_field_choices())
