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

No model has been trained and no accuracy or research conclusion should be
reported until the prepared data, route metadata, target definition, grouped
validation design, and provenance have been reviewed.