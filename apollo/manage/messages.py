# -*- coding: utf-8 -*-
import codecs
import calendar
from datetime import datetime
import sys
from urlparse import urljoin

from flask import current_app, url_for
from flask_script import Command, Option
import pytz
import requests
import unicodecsv


class MessagePlaybackCommand(Command):
    option_list = (
        Option(dest='url'),
        Option(dest='msg_file'),
    )

    def run(self, url, msg_file):
        settings = current_app.config

        if msg_file == '-':
            handle = codecs.getreader('utf-8-sig')(sys.stdin)
        else:
            handle = codecs.open(msg_file, encoding='utf-8-sig')

        with handle:
            reader = unicodecsv.DictReader(handle)
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
