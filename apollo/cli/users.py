"""User CLI options."""

import click
from flask import current_app
from flask.cli import AppGroup, with_appcontext
from flask_security import hash_password

from apollo.core import db, security
from apollo.deployments.models import Deployment
from apollo.users.models import Role

users_cli = AppGroup("users", short_help="User commands.")


def validate_roles(ctx, param, value):
    """Validates provided roles are valid role names."""
    with current_app.app_context():
        roles = [r.name for r in db.session.query(Role).with_entities(Role.name)]

        for role in value:
            if role not in roles:
                raise click.BadParameter(f"{role}. Valid options are: {', '.join(roles)}")

        return value


# TODO: The email address should be validated
@users_cli.command("create")
@with_appcontext
@click.argument("username", type=str)
@click.option("-e", "--email", required=True, prompt="Email address", help="The user's email address.")
@click.option("-f", "--first_name", help="The user's first name.")
@click.option("-l", "--last_name", help="The user's last name.")
@click.option(
    "-r",
    "--role",
    "roles",
    required=True,
    help="The roles to assign to the user (can be specified more than once).",
    multiple=True,
    callback=validate_roles,
)
@click.password_option()
def create_user(username, email, first_name, last_name, roles, password):
    """Create a user account."""
    deployment = db.session.query(Deployment).with_entities(Deployment.id).first()
    user_roles = db.session.query(Role).filter(Role.name.in_(roles)).all()

    if security.datastore.find_user(username=username):
        click.echo("User already exists.")
        return

    new_user = security.datastore.create_user(
        username=username,
        email=email,
        password=hash_password(password),
        roles=user_roles,
        deployment_id=deployment.id,
        first_name=first_name,
        last_name=last_name,
    )

    db.session.add(new_user)
    db.session.commit()
    click.echo(f"User {username} created successfully.")


@users_cli.command("change_password")
@with_appcontext
@click.argument("username", type=str)
@click.password_option()
def change_password(username, password):
    """Change the password of an existing user."""
    user = security.datastore.find_user(username=username)
    if not user:
        click.echo(f"User {username} does not exist.")
        return

    user.set_password(password)
    db.session.commit()
    click.echo(f"Password for user {username} changed successfully.")
