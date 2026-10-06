from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DetectionInput:
    source_path: Path
    source_name: str
    source_stem: str
    manifest_product: str
    group_names: list[str] = field(default_factory=list)
    monitor_names: list[str] = field(default_factory=list)
    monitor_types: list[str] = field(default_factory=list)
    object_names: list[str] = field(default_factory=list)
    value_names: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DetectionCandidate:
    profile_path: Path
    profile_id: str
    score: int
    priority: int
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DetectionCandidateAnalysis:
    profile_path: Path
    profile_id: str
    priority: int
    filename_matches: list[str] = field(default_factory=list)
    group_matches: list[str] = field(default_factory=list)
    monitor_matches: list[str] = field(default_factory=list)
    monitor_type_matches: list[str] = field(default_factory=list)
    raw_score: int = 0
    final_score: int = 0
    candidate: bool = False
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BuildResult:
    input_path: Path
    output_path: Path
    planned_output: bool
    intermediate_path: Path
    intermediate_kept: bool
    profile_path: Path
    profile_id: str
    template_path: Path | None
    template_source: str
    group_count: int
    monitor_count: int
    action_count: int
    validation_checks: list[str]
    input_unchanged: bool
    template_unchanged: bool | None
    dry_run: bool
    validate_only: bool
    dump_model_path: Path | None
    detection_mode: str
    detection_reasons: list[str] = field(default_factory=list)
    output_resolution_log: list[str] = field(default_factory=list)
