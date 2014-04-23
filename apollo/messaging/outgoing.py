from flask import current_app
import requests as r


class Gateway(object):
    """
    Base Gateway class

    :attr gateway_url: Gateway url
    """
    gateway_url = ""

    def send(self, text, recipients):
        raise NotImplementedError


class KannelGateway(Gateway):
    """
    Kannel Gateway class
    """
    def __init__(self, config):
        """
        initializes the kannel gateway object

        :param config: The configuration object obtained from the app settings
        """
        self.gateway_url = config.get('gateway_url')
        self.username = config.get('username')
        self.password = config.get('password')
        self.smsc = config.get('smsc')
        self.charset = config.get('charset')
        self.coding = config.get('coding')

    def send(self, text, recipients, sender=""):
        """
        Sends the message to the specified recipients using this gateway

        :param text: Contents of the text message to send
        :param recipients: An array of all the recipients to send this to
        :param sender: (Optional) sender to set for the message
        """
        gateway_params = {
            'username': self.username,
            'password': self.password,
            'from': sender,
            'to': ','.join(recipients),
            'text': text,
        }
        gateway_params.update(
            dict([(key, getattr(self, key))
                 for key in ['smsc', 'charset', 'coding']
                 if getattr(self, key)]))

        try:
            resp = r.get(self.gateway_url, params=gateway_params)
        except r.ConnectionError:
            return False

        return True if resp.status_code == 202 else False


class TelerivetGateway(Gateway):
    """
    Telerivet Gateway class
    """
    def __init__(self, config):
        """
        initializes the kannel gateway object

        :param config: The configuration object obtained from the app settings
        """
        self.gateway_url = """\
https://api.telerivet.com/v1/projects/%s/messages/outgoing\
""" % config.get('project_id')
        self.api_key = config.get('api_key')
        self.phone_id = config.get('phone_id')
        self.priority = config.get('priority')

    def send(self, text, recipients, sender=""):
        """
        Sends the message to the specified recipients using this gateway

        :param text: Contents of the text message to send
        :param recipients: An array of all the recipients to send this to
        :param sender: (Optional) sender to set for the message
        """
        for recipient in recipients:
            gateway_params = {
                'phone_id': self.phone_id,
                'to_number': recipient,
                'content': text
            }
            gateway_params.update(
                dict([(key, getattr(self, key))
                     for key in ['priority']
                     if getattr(self, key)]))
            try:
                r.post(self.gateway_url, data=gateway_params,
                       auth=(self.api_key, ''))
            except r.ConnectionError:
                pass

        return True


def gateway_factory():
    """
    Factory method for the gateway. Determines the gateway to use from
    the application settings.
    """
    gateway_config = current_app.config.get('MESSAGING_OUTGOING_GATEWAY')
    if gateway_config:
        if gateway_config.get('type') == 'kannel':
            return KannelGateway(gateway_config)
        elif gateway_config.get('type') == 'telerivet':
            return TelerivetGateway(gateway_config)
