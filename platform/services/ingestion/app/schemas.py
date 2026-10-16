"""Pydantic v2 schemas for the ingestion API (strict validation -> HTTP 422)."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    contractor: str | None = Field(default=None, max_length=120)
    budget_at_completion: float = Field(gt=0)
    planned_start: dt.date
    planned_finish: dt.date

    @field_validator("planned_finish")
    @classmethod
    def finish_after_start(cls, v: dt.date, info):
        start = info.data.get("planned_start")
        if start and v < start:
            raise ValueError("planned_finish must be on/after planned_start")
        return v


class ActivityIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1, max_length=48)
    project_id: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    wbs_code: str | None = Field(default=None, max_length=64)
    trade_category: str | None = Field(default=None, max_length=80)
    planned_start: dt.date
    planned_finish: dt.date
    planned_duration_days: float = Field(ge=0)
    budget: float = Field(gt=0)
    total_float_days: float = Field(default=0.0, ge=0)
    predecessor_count: int = Field(default=0, ge=0)
    is_critical: bool = False
    subcontractor_delay_rate: float = Field(default=0.0, ge=0, le=1)


class ProgressUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1, max_length=48)
    timestamp: dt.datetime
    percent_complete: float = Field(ge=0, le=100)
    earned_value: float = Field(ge=0)
    planned_value: float = Field(ge=0)
    notes: str | None = Field(default=None, max_length=400)

    @field_validator("timestamp")
    @classmethod
    def require_tz(cls, v: dt.datetime):
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return v


class CostRecordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1, max_length=48)
    timestamp: dt.datetime
    actual_cost: float
    committed_cost: float = Field(default=0.0, ge=0)

    @field_validator("timestamp")
    @classmethod
    def require_tz(cls, v: dt.datetime):
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return v


class ResourceRecordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1, max_length=48)
    timestamp: dt.datetime
    worker_count: int = Field(default=0, ge=0)
    equipment_utilization: float = Field(default=0.0, ge=0, le=100)
    material_usage_kg: float = Field(default=0.0, ge=0)


class IngestResult(BaseModel):
    inserted: int
    rejected: int
    errors: list[str] = []
