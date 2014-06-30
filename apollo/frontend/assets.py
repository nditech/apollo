from flask.ext.assets import Bundle, Environment

apollo_css = Bundle('css/bootstrap.css',
                    'css/select2.css',
                    'css/select2-bootstrap.css',
                    'css/table-fixed-header.css',
                    'css/datepicker.css',
                    'css/jquery.qtip.css',
                    'css/custom.css',
                    output='css/apollo.css')
apollo_js = Bundle('js/jquery.js',
                   'js/bootstrap.js',
                   'js/select2.js',
                   'js/table-fixed-header.js',
                   'js/bootstrap-datepicker.js',
                   'js/custom.js',
                   output='js/apollo.js')


def init_app(app):
    webassets = Environment(app)
    webassets.register('apollo_css', apollo_css)
    webassets.register('apollo_js', apollo_js)
    webassets.manifest = 'cache' if not app.debug else False
    webassets.cache = not app.debug
    webassets.debug = app.debug
