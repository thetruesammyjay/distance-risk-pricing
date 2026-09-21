from __future__ import annotations

import argparse
from pathlib import Path

from ml.src.futo_survey import load_futo_survey
from ml.src.route_catalog import load_route_catalog
from ml.src.training import run_futo_experiment, save_report

DEFAULT_INPUT = Path(
    "data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv"
)
DEFAULT_OUTPUT = Path("data/processed/futo_model_comparison.json")
DEFAULT_FEATURE_SETS = ("route", "time", "route_time")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare grouped baseline risk classifiers on the FUTO survey."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--route-catalog", type=Path)
    parser.add_argument("--splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset = load_futo_survey(args.input, strict=True)
    route_catalog = None
    feature_sets = DEFAULT_FEATURE_SETS
    if args.route_catalog:
        route_catalog = load_route_catalog(args.route_catalog, strict=True)
        feature_sets = (*DEFAULT_FEATURE_SETS, "route_time_physical")
    report = run_futo_experiment(
        dataset,
        n_splits=args.splits,
        random_state=args.seed,
        feature_sets=feature_sets,
        route_catalog=route_catalog,
    )
    save_report(report, args.output)
    print(f"observations={report.observation_count}")
    print(f"respondents={report.respondent_count}")
    print(f"feature_sets={len(report.experiments)}")
    for experiment in report.experiments:
        print(f"[{experiment.feature_set}] features={len(experiment.feature_names)}")
        for model in experiment.models:
            print(
                f"{model.name}: mean_macro_f1={model.mean_macro_f1:.4f} "
                f"std_macro_f1={model.std_macro_f1:.4f} "
                f"mean_accuracy={model.mean_accuracy:.4f}"
            )
    print(f"report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())