# FUTO survey data source

The first research dataset is the Google Forms export supplied for the Federal
University of Technology, Owerri (FUTO) case study:

`data/raw/FUTO Road Risk Assessment Survey for Dynamic Transportation Pricing.csv`

The export contains 112 respondent rows, 21 named FUTO routes, and five time
bands per route. The 105 route/time responses per respondent produce 11,760
long-format questionnaire observations. The route cells use four labels:
`Low Risk`, `Moderate Risk`, `High Risk`, and `Very High Risk`.

## Interpretation and handling

These are questionnaire-derived perceptions of route risk. They are not verified
accident rates, crime probabilities, or objective danger measurements. They must
remain labelled as `questionnaire` throughout preprocessing and experiments.

The first pipeline excludes demographic columns and free-text comments from the
model feature matrix. They may be analysed separately only with an explicit
research justification and privacy review. A respondent is represented by a
pseudonymous source-row identifier so repeated route/time responses stay in the
same validation group without copying identifying fields into derived data.

The survey names routes and time bands but does not provide route coordinates,
route distances, or route durations. Those features must be joined from a
provenance-documented FUTO route catalog or routing lookup before experiments
that claim to use physical route characteristics.

## Reproducible preparation

From the repository root:

```powershell
uv run python -m scripts.preprocess_futo_survey
```

The command reads the raw export without modifying it and writes the derived
long-format file to `data/interim/`, which is intentionally excluded from Git.
Use `--allow-invalid` only when inspecting a partially valid export; strict mode
is the default for training preparation.

A baseline comparison has now been run using the prepared labels and grouped
validation. Its report is exploratory and must not be treated as evidence of
real-world danger prediction. Physical route features remain pending the route
catalog described below.

## Runtime risk profile

The live prototype consumes a privacy-preserving aggregate rather than the raw
respondent export. Build it with:

```powershell
uv run python -m scripts.build_futo_risk_profile
```

This writes `data/processed/futo_route_risk_profile.csv`, containing one row
per route/time band with its response count, mean ordinal label, and normalized
questionnaire score. The aggregate contains no respondent demographics or
free-text comments and is the file used by `RISK_MODE=futo_survey`.

The runtime provider matches exact route/time profiles where endpoint
coordinates are available. It uses an all-route time prior for surveyed routes
whose endpoints are not yet present in the coordinate collection, and records
that limitation in the API provenance.
## Baseline experiment

The first comparison evaluates route-only, time-band-only, and combined
route/time features with a majority baseline plus unbalanced and class-balanced
logistic regression, constrained decision tree, and constrained random forest
variants. Validation is respondent-grouped and stratified across five folds.
Each fold records a confusion matrix and per-class recall. The generated report
is local and ignored by Git:

`data/processed/futo_model_comparison.json`

These results are exploratory only. The survey target represents perceived route
risk. The aggregate profile is connected to the academic prototype's
questionnaire risk mode, not to a production safety or crime-prediction
system.
