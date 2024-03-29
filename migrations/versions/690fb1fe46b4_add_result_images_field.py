"""add result images field

Revision ID: 690fb1fe46b4
Revises: c4166678fb79
Create Date: 2022-09-05 08:22:51.061235

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "690fb1fe46b4"
down_revision = "c4166678fb79"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "form",
        sa.Column(
            "result_images",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("form", "result_images")
    # ### end Alembic commands ###
