"""finalize daily attendance tracking

Revision ID: c9d0e1f2a3b5
Revises: d0e1f2a3b4c5
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa


revision = "c9d0e1f2a3b5"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("attendance")}
    indexes = {index["name"] for index in inspector.get_indexes("attendance")}
    constraints = {constraint["name"] for constraint in inspector.get_unique_constraints("attendance")}
    if "activity_type" in columns:
        op.alter_column("attendance", "activity_type", existing_type=sa.String(), nullable=True, server_default=None)
    attendance_status = sa.Enum("Present", "Leave", "Absent", name="attendance_status")
    attendance_status.create(bind, checkfirst=True)
    if "date" not in columns:
        op.add_column("attendance", sa.Column("date", sa.Date(), nullable=True))
    if "status" not in columns:
        op.add_column("attendance", sa.Column("status", attendance_status, nullable=True))
    if "uq_attendance_driver_date" not in constraints:
        op.create_unique_constraint("uq_attendance_driver_date", "attendance", ["driver_id", "date"])
    if "ix_attendance_date_status" not in indexes:
        op.create_index("ix_attendance_date_status", "attendance", ["date", "status"])


def downgrade() -> None:
    op.drop_index("ix_attendance_date_status", table_name="attendance")
    op.drop_constraint("uq_attendance_driver_date", "attendance", type_="unique")
    op.drop_column("attendance", "status")
    op.drop_column("attendance", "date")
    sa.Enum(name="attendance_status").drop(op.get_bind(), checkfirst=True)
    op.alter_column("attendance", "activity_type", existing_type=sa.String(), nullable=False,
                    server_default="Attendance / Check-in")
