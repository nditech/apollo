from urlparse import urlunsplit
from flask import current_app, url_for
from flask.ext.script import Command, prompt
import requests
import unicodecsv


class MessagePlaybackCommand(Command):
    def run(self):
        settings = current_app.config

        # construct base url
        hostname = prompt('URL of instance')
        # scheme and other parts
        parts = '', hostname, url_for(
            'messaging.kannel_view'), '', ''
        base_url = urlunsplit(parts)

        filename = prompt('Path to message log')
        with open(filename) as f:
            reader = unicodecsv.DictReader(f)
            for row in reader:
                # ignore outbound messages
                if row['Direction'] == 'OUT':
                    continue

                data = {
                    'sender': row['Mobile'].strip(),
                    'text': row['Text'].strip(),
                    'secret': settings.get('MESSAGING_SECRET')
                }

                requests.get(base_url, params=data)
