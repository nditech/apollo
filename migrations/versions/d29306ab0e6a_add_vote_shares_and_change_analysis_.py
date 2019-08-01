"""Add vote shares and change analysis types

Revision ID: d29306ab0e6a
Revises: 7cef3442efe1
Create Date: 2019-08-01 12:32:48.305478

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.session import Session

from apollo.formsframework.models import Form

# revision identifiers, used by Alembic.
revision = 'd29306ab0e6a'
down_revision = '7cef3442efe1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'form',
        sa.Column('vote_shares', JSONB(astext_type=sa.Text()), nullable=True))

    # a minimal representation of the form table
    form_table = sa.table(
        'form',
        sa.Column('id', sa.Integer()),
        sa.Column('data', JSONB(astext_type=sa.Text())),
        sa.Column('vote_shares', JSONB(astext_type=sa.Text())),
    )

    session = Session(bind=op.get_bind())
    for form in session.query(Form).all():
        vote_shares = []

        for tag in form.tags:
            field = form.get_field_by_tag(tag)
            # replace boolean fields with integer fields
            if field['type'] == 'boolean':
                field['type'] = 'integer'
                field['max'] = 1
                field['min'] = 0

                if field['analysis_type'] == 'PROCESS':
                    # boolean fields now use the 'count' analysis type
                    field['analysis_type'] = 'count'
                else:
                    field['analysis_type'] = 'N/A'
                continue

            if field['analysis_type'] == 'RESULT':
                # don't use process analysis for fields
                # that were marked for results analysis
                # add them to the vote shares instead
                field['analysis_type'] = 'N/A'
                vote_shares.append(tag)
            else:
                if field['type'] in ('multiselect', 'select'):
                    field['analysis_type'] = 'histogram'
                # the integer field type should now use the 'mean' analysis
                # type
                elif field['type'] == 'integer':
                    field['analysis_type'] = 'mean'
                else:
                    field['analysis_type'] = 'N/A'

        # for some reason, couldn't get the ORM to work, so
        # we're using the mapped table object to run the update
        op.execute(
            form_table.update().where(
                form_table.c.id == form.id
            ).values({
                'data': form.data,
                'vote_shares': vote_shares
            })
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    session = Session(bind=op.get_bind())
    form_table = sa.table(
        'form',
        sa.Column('id', sa.Integer()),
        sa.Column('data', JSONB(astext_type=sa.Text())),
    )

    for form in session.query(Form).all():
        for tag in form.vote_shares:
            field = form.get_field_by_tag(tag)
            field['analysis_type'] = 'RESULT'

        for tag in set(form.tags) - set(form.vote_shares):
            field = form.get_field_by_tag(tag)
            if field['analysis_type'] != 'N/A':
                if field['type'] not in ('comment', 'string'):
                    field['analysis_type'] = 'PROCESS'

        op.execute(
            form_table.update().where(form_table.c.id == form.id).values(
                {'data': form.data}
            )
        )
    op.drop_column('form', 'vote_shares')
    # ### end Alembic commands ###
