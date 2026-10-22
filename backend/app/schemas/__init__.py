"""
Schemas de resposta da API. Os campos são snake_case no Python e serializados em camelCase,
no mesmo formato das interfaces do front-end (frontend/src/app/shared/models/).
"""

from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

ExecutionStatus = Literal["success", "failed", "atypical", "running"]
ExecutionTrigger = Literal["scheduled", "manual"]
SimulatedFlow = Literal["login_capture", "otp_only"]
ExecutionFlow = Literal["login_capture", "otp_only", "contract_extraction"]
StepKey = Literal[
    # simulador
    "start_session",
    "otp_captcha",
    "sso_login",
    "lms_access",
    "contract_capture",
    # robô real (ideal_raw_RPA/src/pipeline.py)
    "lms_login",
    "report_download",
    "contract_details",
    "data_upload",
]
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
    flow: SimulatedFlow = "login_capture"
    headless: bool = True


# ---------------------------------------------------------------------------
# Ingestão do robô (/api/rpa/)
# ---------------------------------------------------------------------------


class RpaStepIn(CamelModel):
    key: StepKey
    label: str = Field(max_length=64)


class RpaExecutionStart(CamelModel):
    flow: ExecutionFlow = "contract_extraction"
    trigger: ExecutionTrigger = "manual"
    steps: list[RpaStepIn] = []


class RpaExecutionCreated(CamelModel):
    id: int


class RpaJobClaimed(CamelModel):
    execution_id: int


class RpaJobStatus(CamelModel):
    stop_requested: bool


class RpaStepUpdate(CamelModel):
    status: StepStatus
    duration_seconds: float | None = None


class RpaLogsIn(CamelModel):
    logs: list[LogEntry] = Field(max_length=1000)


class RpaExecutionFinish(CamelModel):
    status: Literal["success", "failed", "atypical"]
    records: int | None = None
    error_title: str | None = Field(default=None, max_length=255)
    error_message: str | None = None


class ContractIn(CamelModel):
    """Um contrato da base Ideal Raw, já consolidado pelo robô (ideal_raw_RPA/src/consolidation)."""

    contract_number: str = Field(min_length=1, max_length=32)
    management_number: str | None = None
    counterparty: str | None = None
    contract_name: str | None = None
    contract_type: str | None = None
    requester: str | None = None
    department: str | None = None
    progress_state: str | None = None
    legal_reviewer: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    review_requested_at: date | None = None
    legal_review_started_at: date | None = None
    review_completed_at: date | None = None
    consent_requested_at: date | None = None
    consent_completed_at: date | None = None
    approval_requested_at: date | None = None
    approval_completed_at: date | None = None
    effective_at: date | None = None
    biz_drop_completed_at: date | None = None
    currency: str | None = Field(default=None, max_length=8)
    amount: float | None = None
    flags: dict[str, bool] = {}
    raw: dict[str, str | None] = {}


class ContractsUpload(CamelModel):
    execution_id: int | None = None
    contracts: list[ContractIn]


class ContractsUploadResult(CamelModel):
    received: int
    created: int
    updated: int


# ---------------------------------------------------------------------------
# Contratos (/api/contracts/)
# ---------------------------------------------------------------------------


class Contract(ContractIn):
    id: int
    last_execution_id: int | None
    updated_at: datetime


class ProgressStateCount(CamelModel):
    progress_state: str | None
    count: int


class ContractSummary(CamelModel):
    total: int
    by_progress_state: list[ProgressStateCount]
    last_updated_at: datetime | None
    last_execution_id: int | None
