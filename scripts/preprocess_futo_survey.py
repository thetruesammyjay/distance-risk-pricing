from __future__ import annotations

import argparse
from pathlib import Path

from ml.src.futo_survey import FutoSurveyValidationError, load_futo_survey, write_long_csv

DEFAULT_INPUT = Path(
    "data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv"
)
DEFAULT_OUTPUT = Path("data/interim/futo_route_risk_observations.csv")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert the FUTO Google Forms export to long format."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="write valid observations while reporting invalid survey cells",
    )
    args = parser.parse_args()
    try:
        dataset = load_futo_survey(args.input, strict=not args.allow_invalid)
    except FutoSurveyValidationError as exc:
        parser.error(str(exc))
    if args.output.resolve() == args.input.resolve():
        parser.error("output must not overwrite the raw input file")
    write_long_csv(dataset, args.output)
    print(f"responses={dataset.response_count}")
    print(f"observations={len(dataset.observations)}")
    print(f"routes={len(dataset.route_ids)}")
    print(f"time_bands={len(dataset.time_bands)}")
    print(f"issues={len(dataset.issues)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())