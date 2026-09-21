from __future__ import annotations

import argparse
from pathlib import Path

from ml.src.futo_survey import load_futo_survey
from ml.src.route_catalog import write_catalog_template

DEFAULT_INPUT = Path(
    "data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv"
)
DEFAULT_OUTPUT = Path("data/external/futo_route_catalog.csv")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a blank, provenance-ready FUTO route metadata template."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dataset = load_futo_survey(args.input, strict=True)
    routes = tuple(
        sorted(
            {
                (observation.route_id, observation.route_name)
                for observation in dataset.observations
            }
        )
    )
    write_catalog_template(routes, args.output)
    print(f"routes={len(routes)}")
    print(f"template={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())