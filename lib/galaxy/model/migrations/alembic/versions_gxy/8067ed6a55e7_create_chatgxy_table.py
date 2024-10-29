"""create chatGXY table

Revision ID: 8067ed6a55e7
Revises: a99a5b52ccb8
Create Date: 2024-10-29 16:59:31.185936

"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
)

from galaxy.model.migrations.util import (
    create_table,
    drop_table,
)

# revision identifiers, used by Alembic.
revision = '8067ed6a55e7'
down_revision = 'a99a5b52ccb8'
branch_labels = None
depends_on = None

table_name= "chatgxy_responses"

def upgrade():
    create_table(
        table_name,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('job.id'), nullable=True),
        Column('response', Text, nullable=False),
        Column('feedback', Integer, nullable=True),
    )


def downgrade():
    drop_table(table_name)
