from functools import wraps
from flask.ext.security.decorators import _get_unauthorized_view


def perm_required(perm):
    '''
    Decorator which specifies that a user must have the specified permission.
    Example::

        @app.route('/create_post')
        @perm_required(Permission(RoleNeed('admin')))
        def create_post():
            return 'Create Post'

    The current user must have the `admin` role in order to view the page.

    :param perm: The specified permission.
    '''
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if perm.can():
                return fn(*args, **kwargs)
            return _get_unauthorized_view()
        return decorated_view
    return wrapper
