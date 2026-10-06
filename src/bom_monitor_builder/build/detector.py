from __future__ import annotations

from pathlib import Path
from typing import Any

from bom_monitor_builder.design_excel.profile_loader import read_profile_data
from bom_monitor_builder.utils.resources import resource_path

from .exceptions import ProfileDetectionError
from .models import DetectionCandidate, DetectionCandidateAnalysis, DetectionInput


def detect_profile(
    detection_input: DetectionInput,
    *,
    profiles_dir: Path | None = None,
) -> DetectionCandidate:
    candidates = rank_profiles(detection_input, profiles_dir=profiles_dir)
    if not candidates or candidates[0].score <= 0:
        raise ProfileDetectionError(
            "No matching profile was found.\n\n"
            "Specify --profile explicitly or add a detection rule to a profile."
        )
    top_score = candidates[0].score
    top_candidates = [candidate for candidate in candidates if candidate.score == top_score]
    if len(top_candidates) > 1:
        profile_list = "\n".join(f"- {candidate.profile_id}" for candidate in top_candidates)
        raise ProfileDetectionError(
            "Profile detection is ambiguous.\n\n"
            "Candidates:\n"
            f"{profile_list}\n\n"
            "Specify --profile explicitly."
        )
    return candidates[0]


def rank_profiles(
    detection_input: DetectionInput,
    *,
    profiles_dir: Path | None = None,
) -> list[DetectionCandidate]:
    resolved_profiles_dir = resource_path(profiles_dir or Path("profiles"))
    candidates: list[DetectionCandidate] = []
    for profile_path in sorted(resolved_profiles_dir.glob("*.yml")):
        profile_data = read_profile_data(profile_path)
        profile_section = profile_data.get("profile", {})
        profile_id = str(profile_section.get("id", profile_path.stem))
        detection_section = profile_data.get("detection", {})
        priority = int(detection_section.get("priority", 0))
        score, reasons = score_profile(detection_input, detection_section)
        total_score = score + priority if score > 0 else 0
        candidates.append(
            DetectionCandidate(
                profile_path=profile_path,
                profile_id=profile_id,
                score=total_score,
                priority=priority,
                reasons=reasons,
            )
        )
    return sorted(candidates, key=lambda item: (item.score, item.priority, item.profile_id), reverse=True)


def analyze_profiles(
    detection_input: DetectionInput,
    *,
    profiles_dir: Path | None = None,
) -> list[DetectionCandidateAnalysis]:
    resolved_profiles_dir = resource_path(profiles_dir or Path("profiles"))
    analyses: list[DetectionCandidateAnalysis] = []
    for profile_path in sorted(resolved_profiles_dir.glob("*.yml")):
        profile_data = read_profile_data(profile_path)
        profile_section = profile_data.get("profile", {})
        profile_id = str(profile_section.get("id", profile_path.stem))
        detection_section = profile_data.get("detection", {})
        priority = int(detection_section.get("priority", 0))
        filename_matches = _matched_patterns(
            detection_section.get("filename_patterns", []),
            [detection_input.source_name, detection_input.source_stem, detection_input.manifest_product],
        )
        group_matches = _matched_patterns(
            detection_section.get("group_name_patterns", []),
            detection_input.group_names,
        )
        monitor_matches = _matched_patterns(
            detection_section.get("monitor_name_patterns", []),
            [*detection_input.monitor_names, *detection_input.object_names, *detection_input.value_names],
        )
        monitor_type_matches = _matched_patterns(
            detection_section.get("monitor_type_patterns", []),
            detection_input.monitor_types,
        )
        raw_score = (len(filename_matches) * 20) + (len(group_matches) * 30) + (len(monitor_matches) * 15)
        if raw_score > 0:
            raw_score += len(monitor_type_matches) * 10
        reasons = [
            *(f"filename:{pattern}" for pattern in filename_matches),
            *(f"group:{pattern}" for pattern in group_matches),
            *(f"monitor:{pattern}" for pattern in monitor_matches),
            *(f"type:{pattern}" for pattern in monitor_type_matches),
        ]
        final_score = raw_score + priority if raw_score > 0 else 0
        analyses.append(
            DetectionCandidateAnalysis(
                profile_path=profile_path,
                profile_id=profile_id,
                priority=priority,
                filename_matches=filename_matches,
                group_matches=group_matches,
                monitor_matches=monitor_matches,
                monitor_type_matches=monitor_type_matches,
                raw_score=raw_score,
                final_score=final_score,
                candidate=final_score > 0,
                reasons=reasons if raw_score > 0 else [],
            )
        )
    return sorted(analyses, key=lambda item: (item.final_score, item.priority, item.profile_id), reverse=True)


def score_profile(
    detection_input: DetectionInput,
    detection_section: dict[str, Any],
) -> tuple[int, list[str]]:
    score = 0
    non_type_score = 0
    reasons: list[str] = []
    filename_score = _match_any(
        detection_section.get("filename_patterns", []),
        [detection_input.source_name, detection_input.source_stem, detection_input.manifest_product],
        20,
        "filename",
        reasons,
    )
    group_score = _match_any(
        detection_section.get("group_name_patterns", []),
        detection_input.group_names,
        30,
        "group",
        reasons,
    )
    monitor_score = _match_any(
        detection_section.get("monitor_name_patterns", []),
        [*detection_input.monitor_names, *detection_input.object_names, *detection_input.value_names],
        15,
        "monitor",
        reasons,
    )
    type_score = _match_any(
        detection_section.get("monitor_type_patterns", []),
        detection_input.monitor_types,
        10,
        "type",
        reasons,
    )
    non_type_score = filename_score + group_score + monitor_score
    if non_type_score <= 0:
        return 0, []
    score = non_type_score + type_score
    return score, reasons


def _match_any(
    patterns: Any,
    values: list[str],
    weight: int,
    label: str,
    reasons: list[str],
) -> int:
    if not isinstance(patterns, list):
        return 0
    normalized_values = [_normalize(value) for value in values if value]
    total = 0
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern.strip():
            continue
        normalized_pattern = _normalize(pattern)
        matched_value = next(
            (value for value in normalized_values if normalized_pattern in value),
            None,
        )
        if matched_value is None:
            continue
        total += weight
        reasons.append(f"{label}:{pattern}")
    return total


def _matched_patterns(
    patterns: Any,
    values: list[str],
) -> list[str]:
    if not isinstance(patterns, list):
        return []
    normalized_values = [_normalize(value) for value in values if value]
    matches: list[str] = []
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern.strip():
            continue
        normalized_pattern = _normalize(pattern)
        if any(normalized_pattern in value for value in normalized_values):
            matches.append(pattern)
    return matches


def _normalize(value: str) -> str:
    return "".join(value.casefold().split())
