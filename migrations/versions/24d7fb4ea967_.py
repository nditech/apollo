"""empty message

Revision ID: 24d7fb4ea967
Revises: 88c83b181af3
Create Date: 2018-03-14 09:09:07.212323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24d7fb4ea967'
down_revision = '88c83b181af3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('participant_data_field', sa.Column('id', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('participant_data_field', 'id')
    # ### end Alembic commands ###
