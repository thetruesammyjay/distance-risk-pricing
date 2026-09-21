# ML research pipeline

This package contains the reproducible data and experiment foundation for the
route-risk research work. It is intentionally separate from the live risk
service.

Current modules:

- `src/contracts.py` defines validated, provenance-aware route/time records.
- `src/preprocessing.py` reads raw CSV files without modifying them and reports
  invalid rows.
- `src/features.py` creates route and UTC time features without including risk
  targets as predictors.
- `src/splitting.py` performs deterministic respondent-grouped train/test
  splitting to prevent leakage from repeated responses.
- `src/evaluation.py` calculates classification metrics from actual predictions.

The FUTO survey is the first empirical dataset supplied for this project. No
trained model artifact is promoted in `models/registry.json`; that registry must
remain empty until a model is reviewed and approved for an experiment or API
inference.

Example use:

```python
from ml.src.preprocessing import preprocess_csv

dataset = preprocess_csv("data/raw/route_observations.csv", strict=True)
```

Raw data must remain untouched. Write any cleaned output to `data/interim/` or
`data/processed/` and record source, license, acquisition date, transformations,
and limitations before training.
## Baseline experiment

With the optional ML extra installed, run the FUTO grouped comparison from the
repository root:

```powershell
uv run --extra ml python -m scripts.train_futo_models
```

The report is written to `data/processed/futo_model_comparison.json`, which is
ignored by Git. The comparison evaluates route-only, time-only, and route-plus-
time feature sets, with unbalanced and `class_weight="balanced"` candidates.
Each run uses five `StratifiedGroupKFold` folds and keeps each pseudonymous
respondent entirely within either training or validation. Fold-level confusion
matrices and per-class recall are included in the report. No trained model
artifact is promoted to the live API by this experiment.