"""Remove FormSet model

Revision ID: 48c96bd323c6
Revises: 7c666157b1bc
Create Date: 2019-02-27 10:09:31.619293

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '48c96bd323c6'
down_revision = '7c666157b1bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('event_form_set_id_fkey', 'event', type_='foreignkey')
    op.drop_column('event', 'form_set_id')
    op.drop_constraint('form_form_set_id_fkey', 'form', type_='foreignkey')
    op.drop_column('form', 'form_set_id')
    op.drop_table('form_set')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('form', sa.Column('form_set_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('form_form_set_id_fkey', 'form', 'form_set', ['form_set_id'], ['id'], ondelete='CASCADE')
    op.add_column('event', sa.Column('form_set_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('event_form_set_id_fkey', 'event', 'form_set', ['form_set_id'], ['id'], ondelete='SET NULL')
    op.create_table('form_set',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('slug', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('deployment_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['deployment_id'], ['deployment.id'], name='form_set_deployment_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='form_set_pkey')
    )
    # ### end Alembic commands ###