import socket
from flask.ext.script import Command, prompt, prompt_pass
from flask.ext.security.forms import RegisterForm
from flask.ext.security.registerable import register_user
from werkzeug.datastructures import MultiDict
from apollo import models, services


class SetupCommand(Command):
    '''A simple command for quickly setting up an Apollo instance'''

    def run(self):
        if models.Deployment.objects.count() > 0:
            print 'You already have deployments set up.'
            return

        name = prompt('Name of new deployment')
        hostname = prompt('Hostname for deployment')

        deployment = models.Deployment.objects.create(
            name=name,
            hostnames=[hostname]
        )

        # create the roles
        role_names = ['manager', 'clerk', 'analyst', 'admin']
        for role_name in role_names:
            role = models.Role.objects.create(name=role_name)

        # create the admin user
        email = prompt('Email for admin user')
        password = prompt_pass('Password for admin user')
        password_confirm = prompt_pass('Confirm password')

        data = MultiDict({
            'email': email,
            'password': password,
            'password_confirm': password_confirm
        })
        form = RegisterForm(data, csrf_enabled=False)
        if form.validate():
            try:
                user = register_user(email=email, password=password)
            except socket.error as e:
                print 'Error sending registration email: {}'.format(e)
                user = services.users.get(email=email, deployment=None)
            user.update(set__deployment=deployment, add_to_set__roles=role)

            print '\nUser created successfully'
            print 'User(id=%s email=%s)' % (user.id, user.email)
        else:
            print '\nError creating user:'
            for errors in form.errors.values():
                print '\n'.join(errors)

        # create at least one event
        from apollo.manage.deployments import CreateEventCommand
        CreateEventCommand._create_event(deployment)
