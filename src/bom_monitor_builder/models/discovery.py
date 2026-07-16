from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    name: str
    display_name: str
    status: str
    startup_type: str
    executable_path: str | None = None


class EventLogInfo(BaseModel):
    channel: str
    provider: str
    event_ids: list[int] = Field(default_factory=list)


class MonitoringCandidate(BaseModel):
    target_type: str
    target_name: str
    relevance_score: int
    reason: str
