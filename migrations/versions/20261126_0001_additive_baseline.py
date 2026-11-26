"""Additive baseline for VISIONARIES SMART KIKOBA V2.
Existing V1 tables and records are preserved. create_all(checkfirst=True) creates only missing tables.
"""
from alembic import op
from app import db
revision = "20261126_0001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    db.metadata.create_all(bind=op.get_bind(), checkfirst=True)
def downgrade():
    # Intentionally non-destructive: production financial records must not be dropped.
    pass
