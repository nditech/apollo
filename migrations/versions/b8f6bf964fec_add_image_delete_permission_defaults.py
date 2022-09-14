"""add image delete permission defaults

Revision ID: b8f6bf964fec
Revises: 690fb1fe46b4
Create Date: 2022-09-14 21:36:55.605913

"""
import itertools
import uuid

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8f6bf964fec"
down_revision = "690fb1fe46b4"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    permission_name = "delete_images"

    # get the deployment ids where the permission does not exist
    query = sa.text("SELECT id FROM deployment")
    result = connection.execute(query)
    deployment_ids = list(itertools.chain(*result.fetchall()))

    # for each deployment, insert the delete image permission
    # if it does not exist
    # NOTE: the loop is necessary since the UUIDs are generated
    #       in Python, not the database
    for deployment_id in deployment_ids:
        select_query = sa.text(
            """
            SELECT id FROM permission
            WHERE name=:name AND deployment_id = :deployment_id
            """
        )
        insert_query = sa.text(
            """
            INSERT INTO permission (name, deployment_id, uuid)
            VALUES (:name, :deployment_id, :uuid) ON CONFLICT DO NOTHING
            RETURNING id
            """
        )
        permission_id = connection.execute(
            select_query, name=permission_name, deployment_id=deployment_id
        ).scalar()
        if permission_id is None:
            permission_id = connection.execute(
                insert_query,
                name=permission_name,
                deployment_id=deployment_id,
                uuid=uuid.uuid4().hex,
            ).scalar()

        roles = ["analyst", "manager"]  # admin already has all permissions
        for role in roles:
            select_query_alt = sa.text(
                """
                SELECT rp.permission_id FROM roles_permissions rp
                JOIN role r ON rp.role_id = r.id
                WHERE rp.permission_id=:permission_id
                AND r.name=:role
                AND r.deployment_id=:deployment_id
                """
            )
            insert_query_alt = sa.text(
                """
                INSERT INTO roles_permissions (role_id, permission_id)
                VALUES (
                    (
                        SELECT id FROM role
                        WHERE deployment_id=:deployment_id
                        AND name=:role
                    ), :permission_id
                )
                """
            )
            permission_id_alt = connection.execute(
                select_query_alt,
                deployment_id=deployment_id,
                permission_id=permission_id,
                role=role,
            )
            if permission_id_alt is None:
                connection.execute(
                    insert_query_alt,
                    deployment_id=deployment_id,
                    permission_id=permission_id,
                    role=role,
                )


def downgrade():
    pass
