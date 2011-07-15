# This file defines some decorators to be used in the project

def role_required(roles):
    ''' role_required is a decorator that is used within the app.py file
    it allows the programmer to restrict what reports should be allowed 
    to be submitted by a particular observer by cross-checking their 
    roles against a submitted list of roles or text containing just a 
    role to be checked'''
    def decorator(f):
        def new_func(*args, **kwargs):
            message = args[1]
            if type(roles) == list or type(roles) == tuple and message.observer.role in roles:
                return f(*args, **kwargs)
            elif message.observer.role == roles:
                return f(*args, **kwargs)
            else:
                return message.respond('You are not permitted to send this report. Please confirm the report you are to send.')
        return new_func
    return decorator
