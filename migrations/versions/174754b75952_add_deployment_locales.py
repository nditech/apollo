"""Add deployment locales

Revision ID: 174754b75952
Revises: 98cab6d3d1d3
Create Date: 2019-01-12 13:07:34.523462

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '174754b75952'
down_revision = '98cab6d3d1d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deployment', sa.Column('primary_locale', sa.String()))
    op.add_column('deployment', sa.Column('other_locales', postgresql.ARRAY(sa.String())))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('deployment', 'primary_locale')
    op.drop_column('deployment', 'other_locales')
    # ### end Alembic commands ###
