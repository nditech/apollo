"""Messages CLI options."""

import calendar
import csv
from datetime import datetime

import click
import pytz
import requests
from flask import current_app, url_for
from flask.cli import AppGroup, with_appcontext

messages_cli = AppGroup("messages", short_help="Message commands.")


@messages_cli.command("replay")
@with_appcontext
@click.argument("source_file", type=click.File())
def replay(source_file):
    """Replays messages stored in a file."""
    injection_url = url_for("messaging.kannel_view", _external=True)

    messages_count = 0

    with source_file:
        reader = csv.DictReader(source_file)
        for row in reader:
            # ensure that all the required columns are present.
            if not all(column_name in row.keys() for column_name in ["Direction", "Created", "Mobile", "Text"]):
                continue

            # ignore outbound messages
            if row["Direction"] == "OUT":
                continue

            message_time = pytz.utc.localize(datetime.strptime(row["Created"], "%Y-%m-%d %H:%M:%S"))

            params = {
                "sender": row["Mobile"].strip(),
                "text": row["Text"].strip(),
                "secret": current_app.config["MESSAGING_SECRET"],
                "timestamp": calendar.timegm(message_time.utctimetuple()),
            }
            requests.get(injection_url, params=params)
            messages_count += 1

    click.echo(f"{messages_count} messages replayed.")
