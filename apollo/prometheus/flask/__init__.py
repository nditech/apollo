import time
from urllib.parse import urlparse, parse_qs

from flask import request
from flask.helpers import make_response
from prometheus_client import core, generate_latest, CONTENT_TYPE_LATEST, Gauge, Histogram, Counter
import flask


def monitor(app):
    def before_request():
        flask.g.start_time = time.time()
        http_concurrent_request_count.inc()

    def after_request(response):
        end_time = time.time()
        request_latency = end_time - getattr(flask.g, 'start_time', end_time)
        http_request_latency_ms.labels(request.method, request.path).observe(request_latency)

        http_concurrent_request_count.dec()

        http_request_count.labels(request.method, request.path, response.status_code).inc()
        return response

    http_request_latency_ms = Histogram('http_request_latency_ms', 'HTTP Request Latency',
                                        ['method', 'endpoint'])

    http_request_count = Counter('http_request_count', 'HTTP Request Count', ['method', 'endpoint', 'http_status'])
    http_concurrent_request_count = Gauge('http_concurrent_request_count', 'Flask Concurrent Request Count')
    app.before_request(before_request)
    app.after_request(after_request)

    if app.config.get('PROMETHEUS_SECRET'):
        app.add_url_rule(
            '/metrics/' + app.config.get('PROMETHEUS_SECRET'),
            'prometheus_metrics', view_func=metrics)


def metrics():
    registry = core.REGISTRY
    params = parse_qs(urlparse(request.path).query)
    if 'name[]' in params:
        registry = registry.restricted_registry(params['name[]'])
    output = generate_latest(registry)
    response = make_response(output)
    response.headers['Content-Type'] = CONTENT_TYPE_LATEST
    return response
