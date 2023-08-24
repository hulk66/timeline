"""empty message

Revision ID: 192e728d2c5d
Revises: b0ffd37de12c
Create Date: 2023-07-17 18:35:33.808498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '192e728d2c5d'
down_revision = 'b0ffd37de12c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('faces', sa.Column('asset_stamp', sa.DateTime(), nullable=True))
    op.execute("update faces f set asset_stamp = (select created from assets a where a.id = f.asset_id) where asset_id is not null")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('faces', 'asset_stamp')
    # ### end Alembic commands ###