from flask import Blueprint, render_template, url_for

core = Blueprint('core', __name__)


@core.route('/')
def index():
    return 'Hello, world!'
