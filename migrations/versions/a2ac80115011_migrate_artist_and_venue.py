"""migrate artist and venue

Revision ID: a2ac80115011
Revises: d2d5cac853ab
Create Date: 2023-03-05 22:26:12.832221

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2ac80115011'
down_revision = 'd2d5cac853ab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Artist', schema=None) as batch_op:
        batch_op.add_column(sa.Column('website', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('seeking_description', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('seeking_venue', sa.Boolean(), nullable=True))

    with op.batch_alter_table('Venue', schema=None) as batch_op:
        batch_op.add_column(sa.Column('genres', sa.ARRAY(sa.String()), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('seeking_talent', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('seeking_description', sa.String(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Venue', schema=None) as batch_op:
        batch_op.drop_column('seeking_description')
        batch_op.drop_column('seeking_talent')
        batch_op.drop_column('website')
        batch_op.drop_column('genres')

    with op.batch_alter_table('Artist', schema=None) as batch_op:
        batch_op.drop_column('seeking_venue')
        batch_op.drop_column('seeking_description')
        batch_op.drop_column('website')

    # ### end Alembic commands ###