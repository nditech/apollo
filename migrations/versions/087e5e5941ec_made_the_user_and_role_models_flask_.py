"""Made the user and role models flask_security compliant.

Revision ID: 087e5e5941ec
Revises: 2f8abed5acd9
Create Date: 2024-10-14 22:33:00.224887

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "087e5e5941ec"
down_revision = "2f8abed5acd9"
branch_labels = None
depends_on = None


def upgrade():
    """Database upgrade migration."""
    usernames_seen = set()
    emails_seen = set()
    duplicate_accounts = set()
    bind = op.get_bind()
    result = bind.execute(sa.text('SELECT username, email FROM "user" ORDER BY id'))
    for row in result:
        if row[0].lower() in usernames_seen or row[1].lower() in emails_seen:
            duplicate_accounts.add(f"{row[0]} ({row[1]})")
        else:
            usernames_seen.add(row[0].lower())
            emails_seen.add(row[1].lower())

    if duplicate_accounts:
        raise Exception(f"Duplicate usernames found: {', '.join(duplicate_accounts)}")

    with op.batch_alter_table("role", schema=None) as batch_op:
        batch_op.alter_column("name", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.create_unique_constraint("role_name_key", ["name"])

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.VARCHAR(64), nullable=True)
        batch_op.alter_column("password", existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.create_unique_constraint("user_email_key", ["email"])
        batch_op.create_unique_constraint("user_username_key", ["username"])


def downgrade():
    """Database downgrade migration."""
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint("user_username_key", type_="unique")
        batch_op.drop_constraint("user_email_key", type_="unique")
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("password", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("username", existing_type=sa.VARCHAR(), nullable=False)

    with op.batch_alter_table("role", schema=None) as batch_op:
        batch_op.drop_constraint("role_name_key", type_="unique")
        batch_op.alter_column("name", existing_type=sa.VARCHAR(), nullable=True)
