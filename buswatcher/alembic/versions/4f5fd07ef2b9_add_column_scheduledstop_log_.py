"""add column scheduledstop_log.interpolated_arrival_flag

Revision ID: 4f5fd07ef2b9
Revises: 
Create Date: 2019-07-17 09:46:42.580532

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f5fd07ef2b9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scheduledstop_log', sa.Column('interpolated_arrival_flag', sa.Boolean))


def downgrade():
    op.drop_column('scheduledstop_log', 'interpolated_arrival_flag')
