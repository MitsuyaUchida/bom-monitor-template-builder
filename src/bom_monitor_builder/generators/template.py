from pathlib import Path

from bom_monitor_builder.models.discovery import MonitoringCandidate


def write_candidate_report(
    candidates: list[MonitoringCandidate],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["target_type,target_name,relevance_score,reason"]

    for candidate in candidates:
        reason = candidate.reason.replace('"', '""')
        lines.append(
            f'{candidate.target_type},{candidate.target_name},'
            f'{candidate.relevance_score},"{reason}"'
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
