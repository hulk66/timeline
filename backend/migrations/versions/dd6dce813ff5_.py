"""empty message

Revision ID: dd6dce813ff5
Revises: 2fafeca904e8
Create Date: 2024-02-12 17:24:02.761003

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'dd6dce813ff5'
down_revision = '2fafeca904e8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('assets', sa.Column('version', sa.Integer(), nullable=True))
    op.add_column('assets', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('assets', sa.Column('checksum', sa.String(length=32), nullable=True))
    op.add_column('assets', sa.Column('checksum_type', sa.String(length=10), nullable=True))
    op.execute("update assets a set version = 1 where version is null")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('assets', 'checksum_type')
    op.drop_column('assets', 'checksum')
    op.drop_column('assets', 'file_size')
    op.drop_column('assets', 'version')
    # ### end Alembic commands ###
