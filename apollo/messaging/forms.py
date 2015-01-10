from .. import services
from flask.ext import wtf
import wtforms


class MessagesFilterForm(wtf.Form):
    mobile = wtforms.StringField()
    text = wtforms.StringField()
    date = wtforms.DateField(format="%d-%m-%Y")


class BaseHttpForm(wtforms.Form):
    '''Helper form for validating incoming messages'''

    def get_message(self):
        return NotImplementedError()


class KannelForm(wtforms.Form):
    '''Django-based form for validating incoming messages
    from a Kannel-based SMS gateway.

    :param sender: The phone number of the sender.
    :param text: The contents of the text message.
    :param charset: (Optional) character set for handling incoming message.
    :param coding: (Optional) not being used at the moment.'''

    sender = wtforms.StringField(validators=[wtforms.validators.required()])
    text = wtforms.StringField(validators=[wtforms.validators.required()])
    charset = wtforms.StringField()
    coding = wtforms.StringField()

    def clean_text(self):
        charset = self.charset.data
        text = self.text.data
        if charset and not isinstance(text, unicode):
            text = text.decode(charset)
        return text.replace('\x00', '')

    def get_message(self):
        if self.validate():
            return {
                'sender': self.sender.data,
                'text': self.clean_text()
            }


class TelerivetForm(BaseHttpForm):
    '''Helper form for validating incoming messages from a
    Telerivet-based SMS gateway.

    The parameters defined here are based on the Telerivet
    [Webhook API](http://telerivet.com/help/api/webhook/receiving)'''

    id = wtforms.StringField()
    from_number = wtforms.StringField(
        validators=[wtforms.validators.required()])
    content = wtforms.StringField(validators=[wtforms.validators.required()])

    def get_message(self):
        if self.validate():
            return {
                'sender': self.from_number.data,
                'text': self.content.data.replace('\x00', '')
            }


def retrieve_form(prefix, form_type='CHECKLIST'):
    '''
    Retrieves a matching form for the given deployment, prefix and form_type.

    :param:`prefix` - The form prefix
    :param:`form_type` - (optional) the form type in narrowing the result
    :returns: a Form document or None
    '''
    current_events = services.events.current_events() \
        or [services.events.default()]

    # find the first form that matches the prefix and optionally form type
    # for the events in the deployment.
    form = services.forms.find(
        events__in=current_events, prefix__iexact=prefix,
        form_type=form_type).first()

    return form
