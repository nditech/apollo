"""add delete images permission

Revision ID: 8ecec40b3815
Revises: c4166678fb79
Create Date: 2022-09-02 16:57:10.844488

"""
import itertools
import uuid

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "8ecec40b3815"
down_revision = "c4166678fb79"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    permission_name = "delete_images"

    # get the deployment ids where the permission does not exist
    query = sa.text(
        """
        SELECT id FROM deployment WHERE id NOT IN (
            SELECT deployment_id FROM permission WHERE name = :name
        )
        """
    )
    result = connection.execute(query, name=permission_name)
    deployment_ids = list(itertools.chain(*result.fetchall()))

    # for each deployment, insert the delete image permission
    # NOTE: the loop is necessary since the UUIDs are generated in Python,
    #       not the database
    for deployment_id in deployment_ids:
        insert_query = sa.text(
            """
            INSERT INTO permission (name, deployment_id, uuid)
            VALUES (:name, :id, :uuid)
            """
        )
        connection.execute(
            insert_query,
            name=permission_name,
            id=deployment_id,
            uuid=uuid.uuid4().hex,
        )


def downgrade():
    pass
