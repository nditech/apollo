from application import app
from core.models import user_datastore
from accounts.views import accounts
from core.views import core
from flask.ext.security import Security

security = Security(app, user_datastore)

app.register_blueprint(accounts, url_prefix='/accounts')
app.register_blueprint(core)

if __name__ == '__main__':
    app.run()
