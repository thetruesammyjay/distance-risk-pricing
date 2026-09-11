from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ml.src.contracts import RiskRecord

REQUIRED_COLUMNS = frozenset(
    {
        "observation_id",
        "respondent_id",
        "route_id",
        "observed_at",
        "origin_latitude",
        "origin_longitude",
        "destination_latitude",
        "destination_longitude",
        "distance_km",
        "duration_minutes",
        "source_type",
    }
)


@dataclass(frozen=True, slots=True)
class PreprocessingIssue:
    row_number: int
    message: str


@dataclass(frozen=True, slots=True)
class PreprocessedDataset:
    records: tuple[RiskRecord, ...]
    issues: tuple[PreprocessingIssue, ...]

    @property
    def accepted_count(self) -> int:
        return len(self.records)

    @property
    def rejected_count(self) -> int:
        return len(self.issues)


class DatasetValidationError(ValueError):
    """Raised when strict preprocessing finds an invalid research record."""


def preprocess_csv(path: str | Path, *, strict: bool = False) -> PreprocessedDataset:
    """Read a CSV without modifying the raw file and validate every record.

    Invalid rows are reported with their CSV row number. Strict mode is useful
    for training jobs because it prevents silently training on a partial file.
    """

    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = frozenset(reader.fieldnames or ())
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise DatasetValidationError(
                f"dataset is missing required columns: {', '.join(missing)}"
            )
        records: list[RiskRecord] = []
        issues: list[PreprocessingIssue] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                records.append(_parse_row(row))
            except (TypeError, ValueError, KeyError) as exc:
                issues.append(PreprocessingIssue(row_number, str(exc)))
        result = PreprocessedDataset(tuple(records), tuple(issues))
    if strict and result.issues:
        summary = "; ".join(f"row {issue.row_number}: {issue.message}" for issue in result.issues)
        raise DatasetValidationError(summary)
    return result


def _parse_row(row: dict[str, Any]) -> RiskRecord:
    return RiskRecord(
        observation_id=_required_text(row, "observation_id"),
        respondent_id=_required_text(row, "respondent_id"),
        route_id=_required_text(row, "route_id"),
        observed_at=_parse_datetime(_required_text(row, "observed_at")),
        origin_latitude=_required_float(row, "origin_latitude"),
        origin_longitude=_required_float(row, "origin_longitude"),
        destination_latitude=_required_float(row, "destination_latitude"),
        destination_longitude=_required_float(row, "destination_longitude"),
        distance_km=_required_float(row, "distance_km"),
        duration_minutes=_required_float(row, "duration_minutes"),
        source_type=_required_text(row, "source_type"),
        accident_risk=_optional_float(row, "accident_risk"),
        road_risk=_optional_float(row, "road_risk"),
        security_risk=_optional_float(row, "security_risk"),
        risk_label=_optional_text(row, "risk_label"),
    )


def _required_text(row: dict[str, Any], name: str) -> str:
    value = row[name]
    if value is None or not str(value).strip():
        raise ValueError(f"{name} is required")
    return str(value).strip()


def _optional_text(row: dict[str, Any], name: str) -> str | None:
    value = row.get(name)
    return None if value is None or not str(value).strip() else str(value).strip()


def _required_float(row: dict[str, Any], name: str) -> float:
    value = row[name]
    if value is None or not str(value).strip():
        raise ValueError(f"{name} is required")
    return float(value)


def _optional_float(row: dict[str, Any], name: str) -> float | None:
    value = row.get(name)
    return None if value is None or not str(value).strip() else float(value)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include timezone information")
    return parsed