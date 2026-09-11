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

There is currently no empirical dataset or trained model in this repository.
`models/registry.json` must remain empty until a real dataset is supplied,
provenance is documented, and an experiment produces a validated artifact.

Example use:

```python
from ml.src.preprocessing import preprocess_csv

dataset = preprocess_csv("data/raw/route_observations.csv", strict=True)
```

Raw data must remain untouched. Write any cleaned output to `data/interim/` or
`data/processed/` and record source, license, acquisition date, transformations,
and limitations before training.