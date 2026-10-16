"""initial 3-tier schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("project_id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("contractor", sa.String(120)),
        sa.Column("budget_at_completion", sa.Float, nullable=False),
        sa.Column("planned_start", sa.Date, nullable=False),
        sa.Column("planned_finish", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "activity",
        sa.Column("activity_id", sa.String(48), primary_key=True),
        sa.Column("project_id", sa.String(32),
                  sa.ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("wbs_code", sa.String(64)),
        sa.Column("trade_category", sa.String(80)),
        sa.Column("planned_start", sa.Date, nullable=False),
        sa.Column("planned_finish", sa.Date, nullable=False),
        sa.Column("planned_duration_days", sa.Float, nullable=False),
        sa.Column("budget", sa.Float, nullable=False),
        sa.Column("total_float_days", sa.Float, server_default="0"),
        sa.Column("predecessor_count", sa.Integer, server_default="0"),
        sa.Column("is_critical", sa.Boolean, server_default=sa.false()),
        sa.Column("subcontractor_delay_rate", sa.Float, server_default="0"),
    )

    op.create_table(
        "progress_update",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(48),
                  sa.ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("percent_complete", sa.Float, nullable=False),
        sa.Column("earned_value", sa.Float, nullable=False),
        sa.Column("planned_value", sa.Float, nullable=False),
        sa.Column("notes", sa.String(400)),
        sa.UniqueConstraint("activity_id", "timestamp", name="uq_progress_activity_ts"),
    )
    op.create_index("ix_progress_activity_ts", "progress_update", ["activity_id", "timestamp"])

    op.create_table(
        "cost_record",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(48),
                  sa.ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_cost", sa.Float, nullable=False),
        sa.Column("committed_cost", sa.Float, server_default="0"),
    )
    op.create_index("ix_cost_activity_ts", "cost_record", ["activity_id", "timestamp"])

    op.create_table(
        "resource_record",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(48),
                  sa.ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("worker_count", sa.Integer, server_default="0"),
        sa.Column("equipment_utilization", sa.Float, server_default="0"),
        sa.Column("material_usage_kg", sa.Float, server_default="0"),
    )
    op.create_index("ix_resource_activity_ts", "resource_record", ["activity_id", "timestamp"])

    op.create_table(
        "kpi_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(48),
                  sa.ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(32),
                  sa.ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pv", sa.Float, nullable=False),
        sa.Column("ev", sa.Float, nullable=False),
        sa.Column("ac", sa.Float, nullable=False),
        sa.Column("cv", sa.Float, nullable=False),
        sa.Column("sv", sa.Float, nullable=False),
        sa.Column("cpi", sa.Float),
        sa.Column("spi", sa.Float),
        sa.Column("eac", sa.Float),
        sa.Column("teac", sa.Float),
    )
    op.create_index("ix_kpi_activity_asof", "kpi_result", ["activity_id", "as_of"])

    op.create_table(
        "risk_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(48),
                  sa.ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.String(32),
                  sa.ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delay_probability", sa.Float, nullable=False),
        sa.Column("risk_category", sa.String(16), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("top_features", sa.String(400)),
    )
    op.create_index("ix_risk_activity_asof", "risk_result", ["activity_id", "as_of"])


def downgrade() -> None:
    for t in ["risk_result", "kpi_result", "resource_record", "cost_record",
              "progress_update", "activity", "project"]:
        op.drop_table(t)
