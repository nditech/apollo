# -*- coding: utf-8 -*-
from flask import (
    Blueprint, Response, g, json, request, session, stream_with_context
)
from flask_security import current_user
from redis import Redis

from apollo.factory import get_redis_pool


sse = Blueprint(__name__, 'sse')


@sse.before_request
def setup_clients():
    if 'sse_redis' not in g or g.sse_redis is None:
        g.sse_redis = Redis(connection_pool=get_redis_pool())

    if 'sse_pubsub' not in g or g.sse_pubsub is None:
        g.sse_pubsub = g.sse_redis.pubsub()


@sse.teardown_request
def teardown_clients(*args, **kwargs):
    pubsub = g.pop('sse_pubsub', None)

    if pubsub:
        pubsub.close()

    # remove the client so it goes
    # out of scope and is returned to the pool
    g.pop('sse_redis', None)


@sse.route('')
def event_stream():
    if not current_user.is_authenticated:
        return '', 404

    channel = request.args.get('channel')
    if not channel or channel != session.get('_id'):
        return '', 404

    g.sse_pubsub.subscribe(channel)

    def generate_stream():
        for message in g.sse_pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    if 'quit' in data:
                        g.sse_pubsub.unsubscribe(channel)
                        break

                    lines = [
                        f'data:{line}'
                        for line in json.dumps(data).splitlines()
                    ]
                    yield '\n'.join(lines) + '\n\n'
                except Exception:
                    g.sse_pubsub.unsubscribe(channel)
                    break

        # yield the last message sent
        if message['type'] == 'message':
            data = json.loads(message['data'])
            lines = [
                f'data:{line}'
                for line in json.dumps(data).splitlines()
            ]
            yield '\n'.join(lines) + '\n\n'

    return Response(
        stream_with_context(generate_stream()),
        headers={
            'Transfer-Encoding': 'identity',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        },
        mimetype='text/event-stream'
    )
