# -*- coding: utf-8 -*-
import calendar
import csv
from datetime import datetime
from urllib.parse import urljoin
from flask import current_app, url_for
from flask_script import Command, prompt
import pytz
import requests


class MessagePlaybackCommand(Command):
    def run(self):
        settings = current_app.config

        # construct base url
        hostname = prompt('URL of current instance')
        base_url = urljoin(hostname, url_for('messaging.kannel_view'))

        filename = prompt('Path to message log')
        with open(filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # ignore outbound messages
                if row['Direction'] == 'OUT':
                    continue

                msg_time = pytz.utc.localize(datetime.strptime(
                    row['Created'],
                    '%Y-%m-%d %H:%M:%S'))

                data = {
                    'sender': row['Mobile'].strip(),
                    'text': row['Text'].strip(),
                    'secret': settings.get('MESSAGING_SECRET'),
                    'timestamp': calendar.timegm(msg_time.utctimetuple())
                }

                requests.get(base_url, params=data)
