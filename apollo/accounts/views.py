from flask import Blueprint, render_template, url_for
from core.models import User

accounts = Blueprint('accounts', __name__, template_folder='templates',
                     static_folder='static')


@accounts.route('/login')
def index():
    return render_template('accounts/login.html')
