"""
Schemas de resposta da API. Os campos são snake_case no Python e serializados em camelCase,
no mesmo formato das interfaces do front-end (frontend/src/app/shared/models/).
"""

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

ExecutionStatus = Literal["success", "failed", "atypical", "running"]
ExecutionTrigger = Literal["scheduled", "manual"]
ExecutionFlow = Literal["login_capture", "otp_only"]
StepKey = Literal["start_session", "otp_captcha", "sso_login", "lms_access", "contract_capture"]
StepStatus = Literal["success", "failed", "running", "pending", "skipped"]
LogLevel = Literal["info", "warning", "error", "success"]
PeriodFilter = Literal["7d", "30d", "all"]
OperationalStatus = Literal["green", "yellow", "red"]

T = TypeVar("T")


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Execution(CamelModel):
    id: int
    flow: ExecutionFlow
    status: ExecutionStatus
    trigger: ExecutionTrigger
    started_at: datetime
    finished_at: datetime | None
    duration_seconds: float | None
    records: int | None


class ExecutionStep(CamelModel):
    key: StepKey
    label: str
    status: StepStatus
    duration_seconds: float | None


class LogEntry(CamelModel):
    timestamp: datetime
    level: LogLevel
    message: str


class ExecutionError(CamelModel):
    title: str
    message: str
    screenshot_url: str | None


class ExecutionDetail(Execution):
    steps: list[ExecutionStep]
    logs: list[LogEntry]
    error: ExecutionError | None


class Page(CamelModel, Generic[T]):
    count: int
    results: list[T]


class StepFailureShare(CamelModel):
    label: str
    percent: float


class UpcomingRun(CamelModel):
    name: str
    scheduled_at: datetime
    source: Literal["cron", "manual"]


class Overview(CamelModel):
    operational_status: OperationalStatus
    status_message: str
    updated_at: datetime
    period_label: str
    running_rate: float
    running_rate_target: float
    total_executions: int
    succeeded: int
    failed: int
    avg_duration_seconds: float
    captured_records: int
    captured_trend: list[int]
    failures_by_step: list[StepFailureShare]
    upcoming_runs: list[UpcomingRun]


class RunRequest(CamelModel):
    flow: ExecutionFlow = "login_capture"
    headless: bool = True
