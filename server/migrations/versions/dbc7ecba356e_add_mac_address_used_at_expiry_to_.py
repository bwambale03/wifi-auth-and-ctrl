"""Add mac_address, used_at, expiry to access_codes and index on code

Revision ID: dbc7ecba356e
Revises: 245fe54affba
Create Date: 2025-05-06 14:07:59.081046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbc7ecba356e'
down_revision = '245fe54affba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('access_codes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mac_address', sa.String(length=17), nullable=False))
        batch_op.add_column(sa.Column('used_at', sa.DateTime(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('access_codes', schema=None) as batch_op:
        batch_op.drop_column('used_at')
        batch_op.drop_column('mac_address', nullable=True)

    # ### end Alembic commands ###
