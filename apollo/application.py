import urlparse
from flask import Flask, g, request
from flask.ext.babel import Babel
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface

app = Flask(__name__)
app.debug = True
app.config.from_pyfile('application.cfg', silent=True)

# set up database
db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)

# set up i18n
babel = Babel(app)


@app.before_request
def select_deployment():
    from core.models import Deployment
    hostname = urlparse.urlparse(request.url).hostname
    try:
        g.deployment = Deployment.objects.get(hostnames=hostname)
    except Deployment.DoesNotExist:
        g.deployment = None
