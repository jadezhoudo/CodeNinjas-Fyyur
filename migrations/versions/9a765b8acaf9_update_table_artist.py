"""update table artist

Revision ID: 9a765b8acaf9
Revises: a2ac80115011
Create Date: 2023-03-11 14:27:44.219250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a765b8acaf9'
down_revision = 'a2ac80115011'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Artist', schema=None) as batch_op:
        batch_op.add_column(sa.Column('genres', sa.String(length=120), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Artist', schema=None) as batch_op:
        batch_op.drop_column('genres')

    # ### end Alembic commands ###