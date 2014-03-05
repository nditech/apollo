from django import forms


class BaseHttpForm(forms.Form):
    '''Helper form for validating incoming messages'''

    def get_message(self):
        return NotImplementedError()


class KannelForm(forms.Form):
    '''Django-based form for validating incoming messages
    from a Kannel-based SMS gateway.

    :param sender: The phone number of the sender.
    :param text: The contents of the text message.
    :param charset: (Optional) character set for handling incoming message.
    :param coding: (Optional) not being used at the moment.'''

    sender = forms.CharField()
    text = forms.CharField()
    charset = forms.CharField(required=False)
    coding = forms.CharField(required=False)

    def clean_text(self):
        charset = self.cleaned_data.get('charset')
        text = self.cleaned_data.get('text')
        if charset and not isinstance(text, unicode):
            text = text.decode(charset)
        return text

    def get_message(self):
        if self.is_valid():
            return {
                'sender': self.cleaned_data.get('sender'),
                'text': self.cleaned_data.get('text')
            }


class TelerivetForm(BaseHttpForm):
    '''Helper form for validating incoming messages from a
    Telerivet-based SMS gateway.

    The parameters defined here are based on the Telerivet
    [Webhook API](http://telerivet.com/help/api/webhook/receiving)'''

    id = forms.CharField()
    from_number = forms.CharField()
    content = forms.CharField()

    def get_message(self):
        if self.is_valid():
            return {
                'sender': self.cleaned_data.get('from_number'),
                'text': self.cleaned_data.get('content')
            }
