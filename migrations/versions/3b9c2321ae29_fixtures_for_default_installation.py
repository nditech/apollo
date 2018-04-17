"""fixtures for default installation

Revision ID: 3b9c2321ae29
Revises: 49879d5c432a
Create Date: 2018-04-17 12:54:58.330213

"""
from alembic import op
from apollo.frontend import permissions
from flask_principal import Permission


# revision identifiers, used by Alembic.
revision = '3b9c2321ae29'
down_revision = '49879d5c432a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""INSERT INTO deployment (
        id, name, hostnames, allow_observer_submission_edit,
        include_rejected_in_votes, is_initialized, dashboard_full_locations) 
        VALUES (1, 'Default', '{\"localhost\"}', 't', 'f', 'f', 't')""")
    op.execute("""INSERT INTO resource (
        resource_id, resource_type, deployment_id)
        VALUES (1, 'event', 1)""")
    op.execute("""INSERT INTO event (
        id, name, start, \"end\", resource_id)
        VALUES (1, 'Default', '1970-01-01 00:00:00', '1970-01-01 00:00:00', 1)
        """)
    op.execute("""INSERT INTO role (
        id, deployment_id, name) VALUES (1, 1, 'admin')""")
    op.execute("""INSERT INTO role (
        id, deployment_id, name) VALUES (2, 1, 'analyst')""")
    op.execute("""INSERT INTO role (
        id, deployment_id, name) VALUES (3, 1, 'manager')""")
    op.execute("""INSERT INTO role (
        id, deployment_id, name) VALUES (4, 1, 'clerk')""")
    op.execute("""INSERT INTO \"user\" (
        id, deployment_id, email, username, password, active)
        VALUES (1, 1, 'root@localhost', 'admin',
        '$pbkdf2-sha256$29000$mPN.751zjhGCUKqVMmZMSQ$3/RCkmdZaTa6PTAtgimPMB4tIheE/Yz/1tAM/yVRgkQ',
        't')""")
    op.execute("INSERT INTO roles_users (user_id, role_id) VALUES (1, 1)")

    for name in dir(permissions):
        item = getattr(permissions, name, None)
        if isinstance(item, Permission):
            for need in item.needs:
                if need.method == 'action':
                    op.execute("""INSERT INTO permission (name, deployment_id)
                               VALUES ('%s', 1)""" % need.value)


def downgrade():
    op.execute('DELETE FROM permission WHERE deployment_id=1')
    op.execute('DELETE FROM roles_users WHERE user_id=1')
    op.execute('DELETE FROM \"user\" WHERE id=1')
    op.execute('DELETE FROM role WHERE deployment_id=1')
    op.execute('DELETE FROM event WHERE id=1')
    op.execute('DELETE FROM resource WHERE resource_id=1')
    op.execute('DELETE FROM deployment WHERE id=1')
