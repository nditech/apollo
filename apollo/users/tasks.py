# -*- coding: utf-8 -*-
import os

import pandas as pd
from celery import shared_task
from flask_babel import gettext
from sqlalchemy import func

from apollo import helpers
from apollo.core import uploads
from apollo.settings import LANGUAGES
from apollo.users.models import Role, User, UserUpload


def _is_valid(item):
    return not pd.isnull(item) and item


@shared_task(bind=True)
def import_users(task, upload_id: int, mappings: dict, channel: str = None):
    """Import user accounts."""
    upload = UserUpload.query.filter(UserUpload.id == upload_id).first()

    if not upload:
        return

    file_path = uploads.path(upload.upload_filename)
    if not os.path.exists(file_path):
        upload.delete()
        return

    with open(file_path, "rb") as f:
        dataframe = helpers.load_source_file(f)

    total_records = dataframe.shape[0]
    processed_records = 0
    error_records = 0
    warning_records = 0
    error_log = []

    USERNAME_COL = mappings.get("username")
    EMAIL_COL = mappings.get("email")
    PASSWORD_COL = mappings.get("password")
    ROLE_COL = mappings.get("role")
    LOCALE_COL = mappings.get("lang")
    FIRST_NAME_COL = mappings.get("first_name")
    LAST_NAME_COL = mappings.get("last_name")
    VALID_LANGUAGE_CODES = set(LANGUAGES.keys())

    for idx in dataframe.index:
        current_row = dataframe.iloc[idx]
        username = current_row.get(USERNAME_COL)
        email = current_row.get(EMAIL_COL)
        password = current_row.get(PASSWORD_COL)
        role_name = current_row.get(ROLE_COL)
        locale = current_row.get(LOCALE_COL)
        first_name = current_row.get(FIRST_NAME_COL)
        last_name = current_row.get(LAST_NAME_COL)

        # email is required
        if not _is_valid(email):
            error_log.append(
                {
                    "label": "ERROR",
                    "message": gettext("No valid email found"),
                }
            )
            error_records += 1
            continue

        # find user by email, or create one
        user = User.query.filter(
            User.deployment_id == upload.deployment_id,
            func.lower(User.email) == func.lower(str(email)),
        ).first()
        if user is None:
            user = User(deployment_id=upload.deployment_id, email=email)

        # update username if exists
        if _is_valid(username):
            user.username = str(username)

        # password is required for a new user
        if not _is_valid(password) and user.id is None:
            error_log.append(
                {
                    "label": "ERROR",
                    "message": gettext("New user has no password set"),
                }
            )
            error_records += 1
            continue
        user.set_password(str(password))

        if _is_valid(role_name):
            role = Role.get_by_name(str(role_name))
            if role is not None:
                user.roles = [role]

        if _is_valid(locale) and str(locale) in VALID_LANGUAGE_CODES:
            user.locale = str(locale)

        if _is_valid(first_name):
            user.first_name = str(first_name)

        if _is_valid(last_name):
            user.last_name = str(last_name)

        user.save()
        processed_records += 1
        task.update_state(
            state="PROGRESS",
            meta={
                "total_records": total_records,
                "processed_records": processed_records,
                "error_records": error_records,
                "warning_records": warning_records,
                "error_log": error_log,
            },
        )

    os.remove(file_path)
    upload.delete()
