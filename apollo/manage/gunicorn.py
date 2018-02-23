# -*- coding: utf-8 -*-
from flask_script import Command, Option


class GunicornServer(Command):

    description = "Run the app within gunicorn"

    def get_options(self):
        from gunicorn.config import make_settings

        settings = make_settings()
        options = (
            Option(*klass.cli, dest=klass.name, default=klass.default)
            for setting, klass in settings.items() if klass.cli
        )
        return options

    def __call__(self, app=None, *args, **kwargs):
        from gunicorn.app.base import Application

        class FlaskApplication(Application):
            def init(self, parser, opts, args):
                return kwargs

            def load(self):
                return app

        FlaskApplication().run()
