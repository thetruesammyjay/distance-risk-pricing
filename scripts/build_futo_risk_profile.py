from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from ml.src.futo_survey import load_futo_survey

DEFAULT_INPUT = Path(
    "data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv"
)
DEFAULT_OUTPUT = Path("data/processed/futo_route_risk_profile.csv")
PROFILE_COLUMNS = (
    "route_id",
    "route_name",
    "time_band",
    "response_count",
    "mean_risk_ordinal",
    "risk_score",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an aggregate, privacy-preserving FUTO route/time risk profile."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("output must not overwrite the raw input file")

    dataset = load_futo_survey(args.input, strict=True)
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    names: dict[str, str] = {}
    for observation in dataset.observations:
        groups[(observation.route_id, observation.time_band)].append(observation.risk_ordinal)
        names[observation.route_id] = observation.route_name

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        for (route_id, time_band), ordinals in sorted(groups.items()):
            mean_ordinal = Decimal(sum(ordinals)) / Decimal(len(ordinals))
            # Map the four ordinal label bands to their midpoints in [0, 1].
            risk_score = ((mean_ordinal - Decimal("0.5")) / Decimal("4")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            writer.writerow(
                {
                    "route_id": route_id,
                    "route_name": names[route_id],
                    "time_band": time_band,
                    "response_count": len(ordinals),
                    "mean_risk_ordinal": f"{mean_ordinal:.4f}",
                    "risk_score": f"{risk_score:.4f}",
                }
            )
    print(f"responses={dataset.response_count}")
    print(f"observations={len(dataset.observations)}")
    print(f"profile_rows={len(groups)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
