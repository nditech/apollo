from accounts.views import accounts
from application import app
from core.models import user_datastore
from core.views import core
from flask.ext.babel import Babel
from flask.ext.security import Security
from flask.ext.assets import Bundle, Environment

babel = Babel(app)
security = Security(app, user_datastore)

apollo_css = Bundle('core/css/bootstrap.css',
                    'core/css/select2.css',
                    'core/css/table-fixed-header.css',
                    'core/css/datepicker.css',
                    'core/css/jquery.qtip.css',
                    'core/css/custom.css', output='css/apollo.css')
apollo_js = Bundle('core/js/jquery.js',
                   'core/js/bootstrap.js',
                   'core/js/select2.js',
                   'core/js/table-fixed-header.js',
                   'core/js/bootstrap-datepicker.js',
                   'core/js/custom.js', output='js/apollo.js')

assets = Environment(app)
assets.register('apollo_css', apollo_css)
assets.register('apollo_js', apollo_js)

app.register_blueprint(core)
app.register_blueprint(accounts, url_prefix='/accounts')
