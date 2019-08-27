# -*- coding: utf-8 -*-
from flask import Blueprint, request, Response, current_app
from flask_security import login_required, roles_required
from gevent import Timeout

from apollo.core import red
from ..frontend import route


class ServerSideEvent(object):
    def __init__(self, data, event=None, identifier=None, retry=None):
        self.data = data if not type(
            data) == bytes else data.decode(errors='replace')
        self.event = event
        self.id = identifier
        self.retry = retry
        self.desc_map = {
            "event": self.event,
            "id": self.id,
            "retry": self.retry
        }

    def encode(self):
        if not self.data:
            return ":\n\n"
        lines = ["%s: %s" % (k, v) for k, v in self.desc_map.items() if v]
        lines.extend(["data: %s" % v for v in self.data.split("\n")])

        return "%s\n\n" % "\n".join(lines)

    def __repr__(self):
        return self.encode()


bp = Blueprint('sse', __name__)


@route(bp, '/stream', methods=['GET'])
@login_required
@roles_required('admin')
def stream():
    config = current_app.config
    channel = request.args.get('channel', 'apollo')

    def stream_events():
        while True:
            pubsub = red.pubsub()
            pubsub.subscribe(channel)

            try:
                with Timeout(config.get('KEEPALIVE_INTERVAL', 15)) as timeout:
                    for message in pubsub.listen():
                        if message['type'] == 'message':
                            yield ServerSideEvent(message['data']).encode()
                            timeout.cancel()
                            timeout.start()
            except Timeout as t:
                if t is not timeout:
                    raise
                else:
                    yield ServerSideEvent('').encode()

    res = Response(stream_events(), mimetype='text/event-stream')

    return res
