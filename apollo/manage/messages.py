# -*- coding: utf-8 -*-
import calendar
import csv
from datetime import datetime
import io
import sys
from urllib.parse import urljoin

from flask import current_app, url_for
from flask_script import Command, Option
import pytz
import requests


class MessagePlaybackCommand(Command):
    option_list = (
        Option(dest='url'),
        Option(dest='msg_file'),
    )

    def run(self, url, msg_file):
        settings = current_app.config

        if msg_file == '-':
            handle = io.TextIOWrapper(sys.stdin.buffer, 'utf-8-sig')
        else:
            handle = open(msg_file)

        with handle:
            reader = csv.DictReader(handle)
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

                requests.get(url, params=data)
