"""Add verified fields attribute

Revision ID: 7cef3442efe1
Revises: 312d87e3ca88
Create Date: 2019-07-15 15:20:01.405244

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7cef3442efe1'
down_revision = '312d87e3ca88'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submission', sa.Column('verified_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    connection = op.get_bind()
    query = sa.sql.text('''
        UPDATE submission
        SET verified_fields = '[]'::jsonb
        WHERE verified_fields IS NULL;
    ''')
    connection.execute(query)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submission', 'verified_fields')
    # ### end Alembic commands ###