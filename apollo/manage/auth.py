# -*- coding: utf-8 -*-
import click
from flask_script import Command
from flask_security.utils import hash_password

from apollo.core import db
from apollo.deployments.models import Deployment
from apollo.users.models import Role, User


class CreateUserCommand(Command):
    """Create a user"""

    def run(self):
        deployments = Deployment.query.order_by(Deployment.name).all()
        click.echo("----- DEPLOYMENTS -----")
        for idx, deployment in enumerate(deployments, 1):
            click.echo(f"({idx}) - {deployment.name}")
        index = click.prompt(
            "Select deployment", type=click.IntRange(1, len(deployments))
        )
        deployment = deployments[index - 1]

        email = click.prompt("Email")
        username = click.prompt("Username")
        password = None
        password_confirm = None

        while True:
            password = click.prompt("Password", hide_input=True)
            password_confirm = click.prompt(
                "Confirm password", hide_input=True
            )

            if password and password == password_confirm:
                break
            click.echo("Passwords do not match", err=True)

        roles = (
            Role.query.filter(Role.deployment == deployment)
            .order_by(Role.name)
            .all()
        )
        click.echo("----- ROLES -----")
        for idx, role in enumerate(roles, 1):
            click.echo(f"({idx}) - {role.name}")
        index = click.prompt("Select role", type=click.IntRange(1, len(roles)))
        role = roles[index - 1]

        # verify that username and email are unique for the deployment
        subquery = User.query.filter(
            User.username == username, User.deployment == deployment
        )
        username_used = db.session.query(subquery.exists()).scalar()

        if username_used:
            click.echo(f"Username ({username}) is already in use", err=True)
            return

        subquery = User.query.filter(
            User.email == email, User.deployment == deployment
        )
        email_used = db.session.query(subquery.exists()).scalar()

        if email_used:
            click.echo(f"Email ({email}) is already in use", err=True)
            return

        # create user
        user = User(
            deployment=deployment,
            email=email,
            password=hash_password(password),
            username=username,
        )
        user.roles = [role]
        user.save()
        click.echo("User created successfully")
