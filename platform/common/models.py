"""SQLAlchemy ORM models: the 3-tier relational schema (paper Sec. IV-B).

Tiers
-----
Master Entities       : Project, Activity
Time-Series Facts     : ProgressUpdate, CostRecord, ResourceRecord
Computed Output Tables: KPIResult, RiskResult
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------- #
# Master entities
# --------------------------------------------------------------------------- #
class Project(Base):
    __tablename__ = "project"

    project_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contractor: Mapped[str | None] = mapped_column(String(120))
    budget_at_completion: Mapped[float] = mapped_column(Float, nullable=False)
    planned_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    planned_finish: Mapped[dt.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Activity(Base):
    __tablename__ = "activity"

    activity_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    wbs_code: Mapped[str | None] = mapped_column(String(64))
    trade_category: Mapped[str | None] = mapped_column(String(80))
    planned_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    planned_finish: Mapped[dt.date] = mapped_column(Date, nullable=False)
    planned_duration_days: Mapped[float] = mapped_column(Float, nullable=False)
    budget: Mapped[float] = mapped_column(Float, nullable=False)  # BAC per activity
    total_float_days: Mapped[float] = mapped_column(Float, default=0.0)
    predecessor_count: Mapped[int] = mapped_column(Integer, default=0)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    subcontractor_delay_rate: Mapped[float] = mapped_column(Float, default=0.0)

    project: Mapped[Project] = relationship(back_populates="activities")
    progress_updates: Mapped[list["ProgressUpdate"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )
    cost_records: Mapped[list["CostRecord"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# Time-series fact records (append-only)
# --------------------------------------------------------------------------- #
class ProgressUpdate(Base):
    __tablename__ = "progress_update"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    percent_complete: Mapped[float] = mapped_column(Float, nullable=False)  # 0..100
    earned_value: Mapped[float] = mapped_column(Float, nullable=False)  # EV
    planned_value: Mapped[float] = mapped_column(Float, nullable=False)  # PV at this time
    notes: Mapped[str | None] = mapped_column(String(400))

    activity: Mapped[Activity] = relationship(back_populates="progress_updates")

    __table_args__ = (
        Index("ix_progress_activity_ts", "activity_id", "timestamp"),
        UniqueConstraint("activity_id", "timestamp", name="uq_progress_activity_ts"),
    )


class CostRecord(Base):
    __tablename__ = "cost_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_cost: Mapped[float] = mapped_column(Float, nullable=False)  # AC (incremental)
    committed_cost: Mapped[float] = mapped_column(Float, default=0.0)

    activity: Mapped[Activity] = relationship(back_populates="cost_records")

    __table_args__ = (Index("ix_cost_activity_ts", "activity_id", "timestamp"),)


class ResourceRecord(Base):
    __tablename__ = "resource_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    worker_count: Mapped[int] = mapped_column(Integer, default=0)
    equipment_utilization: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100
    material_usage_kg: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (Index("ix_resource_activity_ts", "activity_id", "timestamp"),)


# --------------------------------------------------------------------------- #
# Computed output tables
# --------------------------------------------------------------------------- #
class KPIResult(Base):
    __tablename__ = "kpi_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False
    )
    as_of: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    pv: Mapped[float] = mapped_column(Float, nullable=False)
    ev: Mapped[float] = mapped_column(Float, nullable=False)
    ac: Mapped[float] = mapped_column(Float, nullable=False)
    cv: Mapped[float] = mapped_column(Float, nullable=False)
    sv: Mapped[float] = mapped_column(Float, nullable=False)
    cpi: Mapped[float | None] = mapped_column(Float)
    spi: Mapped[float | None] = mapped_column(Float)
    eac: Mapped[float | None] = mapped_column(Float)
    teac: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (Index("ix_kpi_activity_asof", "activity_id", "as_of"),)


class RiskResult(Base):
    __tablename__ = "risk_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("activity.activity_id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False
    )
    as_of: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    delay_probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0..1
    risk_category: Mapped[str] = mapped_column(String(16), nullable=False)  # Low/Medium/High
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    top_features: Mapped[str | None] = mapped_column(String(400))  # JSON string

    __table_args__ = (Index("ix_risk_activity_asof", "activity_id", "as_of"),)
