"""Change event start and end column types

Revision ID: 2d9011b4a9f0
Revises: e072b671cf70
Create Date: 2019-01-05 16:21:12.939983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d9011b4a9f0'
down_revision = 'e072b671cf70'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('event', 'start', type_=sa.DateTime(timezone=True))
    op.alter_column('event', 'end', type_=sa.DateTime(timezone=True))


def downgrade():
    op.alter_column('event', 'start', type_=sa.DateTime())
    op.alter_column('event', 'end', type_=sa.DateTime())
