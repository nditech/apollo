"""added turnout_fields to the forms model

Revision ID: 69c602dc37b2
Revises: b8f6bf964fec
Create Date: 2022-12-06 05:35:07.028885

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '69c602dc37b2'
down_revision = 'b8f6bf964fec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form', sa.Column('turnout_fields', postgresql.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('form', 'turnout_fields')
    # ### end Alembic commands ###
