from flask import Flask
from flask.ext.mongoengine import MongoEngine, MongoEngineSessionInterface

app = Flask(__name__)
app.debug = True
app.config.from_pyfile('application.cfg', silent=True)

db = MongoEngine(app)
app.session_interface = MongoEngineSessionInterface(db)
