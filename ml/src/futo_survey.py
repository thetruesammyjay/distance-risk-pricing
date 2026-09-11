from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

FUTO_SOURCE_TYPE = "questionnaire"
FUTO_RISK_ORDINALS = {
    "Low Risk": 1,
    "Moderate Risk": 2,
    "High Risk": 3,
    "Very High Risk": 4,
}
ROUTE_HEADER_PATTERN = re.compile(r"^Route:\s*(?P<route>.+?)\s*\[(?P<time_band>[^]]+)\]\s*$")


@dataclass(frozen=True, slots=True)
class FutoSurveyObservation:
    """One long-format, questionnaire-derived FUTO route/time response."""

    observation_id: str
    respondent_id: str
    route_id: str
    route_name: str
    time_band: str
    risk_label: str
    risk_ordinal: int
    source_type: str = FUTO_SOURCE_TYPE


@dataclass(frozen=True, slots=True)
class FutoSurveyIssue:
    row_number: int
    column: str
    message: str


@dataclass(frozen=True, slots=True)
class FutoSurveyDataset:
    observations: tuple[FutoSurveyObservation, ...]
    response_count: int
    issues: tuple[FutoSurveyIssue, ...]

    @property
    def route_ids(self) -> tuple[str, ...]:
        return tuple(sorted({observation.route_id for observation in self.observations}))

    @property
    def time_bands(self) -> tuple[str, ...]:
        return tuple(sorted({observation.time_band for observation in self.observations}))

    @property
    def respondent_ids(self) -> tuple[str, ...]:
        return tuple(sorted({observation.respondent_id for observation in self.observations}))


class FutoSurveyValidationError(ValueError):
    """Raised when strict FUTO survey parsing finds an invalid response."""


def load_futo_survey(path: str | Path, *, strict: bool = True) -> FutoSurveyDataset:
    """Convert a Google Forms wide export into a validated long-format dataset.

    Each source row represents one respondent. A pseudonymous row identifier is
    used as the grouping key because the form export has no respondent ID. The
    raw export is read only; this function never rewrites it.
    """

    source_path = Path(path)
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        route_columns = _route_columns(fieldnames)
        if "Timestamp" not in fieldnames:
            raise FutoSurveyValidationError("dataset must contain a Timestamp column")
        if not route_columns:
            raise FutoSurveyValidationError("dataset must contain at least one Route: column")

        observations: list[FutoSurveyObservation] = []
        issues: list[FutoSurveyIssue] = []
        response_count = 0
        for row_number, row in enumerate(reader, start=2):
            response_count += 1
            respondent_id = f"futo-respondent-{response_count:04d}"
            if not str(row.get("Timestamp", "")).strip():
                issues.append(FutoSurveyIssue(row_number, "Timestamp", "timestamp is required"))
            for column, route_name, time_band in route_columns:
                label = str(row.get(column, "")).strip()
                if label not in FUTO_RISK_ORDINALS:
                    issues.append(
                        FutoSurveyIssue(
                            row_number,
                            column,
                            f"unsupported risk response: {label or '<blank>'}",
                        )
                    )
                    continue
                route_id = _slug(route_name)
                observation_id = f"{respondent_id}-{route_id}-{_slug(time_band)}"
                observations.append(
                    FutoSurveyObservation(
                        observation_id=observation_id,
                        respondent_id=respondent_id,
                        route_id=route_id,
                        route_name=route_name,
                        time_band=time_band,
                        risk_label=label,
                        risk_ordinal=FUTO_RISK_ORDINALS[label],
                    )
                )
    result = FutoSurveyDataset(tuple(observations), response_count, tuple(issues))
    if strict and result.issues:
        summary = "; ".join(
            f"row {issue.row_number}, {issue.column}: {issue.message}" for issue in result.issues
        )
        raise FutoSurveyValidationError(summary)
    return result


def write_long_csv(dataset: FutoSurveyDataset, path: str | Path) -> None:
    """Write derived observations to an interim/processed path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "observation_id",
        "respondent_id",
        "route_id",
        "route_name",
        "time_band",
        "risk_label",
        "risk_ordinal",
        "source_type",
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for observation in dataset.observations:
            writer.writerow({name: getattr(observation, name) for name in fieldnames})


def _route_columns(fieldnames: tuple[str, ...]) -> tuple[tuple[str, str, str], ...]:
    parsed: list[tuple[str, str, str]] = []
    for column in fieldnames:
        match = ROUTE_HEADER_PATTERN.match(column.strip())
        if match:
            parsed.append(
                (
                    column,
                    _clean_text(match.group("route")),
                    _clean_text(match.group("time_band")),
                )
            )
    return tuple(parsed)


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"