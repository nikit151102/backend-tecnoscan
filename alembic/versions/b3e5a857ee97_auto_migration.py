"""auto migration

Revision ID: b3e5a857ee97
Revises: 81799917d5a1
Create Date: 2025-04-14 10:44:15.392173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3e5a857ee97'
down_revision: Union[str, None] = '81799917d5a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('application', sa.Column('car_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.drop_constraint('application_brand_id_fkey', 'application', type_='foreignkey')
    op.drop_constraint('application_transmission_type_id_fkey', 'application', type_='foreignkey')
    op.drop_constraint('application_engine_volume_fkey', 'application', type_='foreignkey')
    op.create_foreign_key(None, 'application', 'car', ['car_id'], ['id'])
    op.drop_column('application', 'model')
    op.drop_column('application', 'brand_id')
    op.drop_column('application', 'year')
    op.drop_column('application', 'transmission_type_id')
    op.drop_column('application', 'vin_code')
    op.drop_column('application', 'engine_volume')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('application', sa.Column('engine_volume', postgresql.UUID(), autoincrement=False, nullable=False))
    op.add_column('application', sa.Column('vin_code', sa.VARCHAR(length=17), autoincrement=False, nullable=False))
    op.add_column('application', sa.Column('transmission_type_id', postgresql.UUID(), autoincrement=False, nullable=False))
    op.add_column('application', sa.Column('year', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('application', sa.Column('brand_id', postgresql.UUID(), autoincrement=False, nullable=False))
    op.add_column('application', sa.Column('model', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'application', type_='foreignkey')
    op.create_foreign_key('application_engine_volume_fkey', 'application', 'engine_vol', ['engine_volume'], ['id'])
    op.create_foreign_key('application_transmission_type_id_fkey', 'application', 'transmission_types', ['transmission_type_id'], ['id'])
    op.create_foreign_key('application_brand_id_fkey', 'application', 'car_brand', ['brand_id'], ['id'])
    op.drop_column('application', 'car_id')
    # ### end Alembic commands ###
