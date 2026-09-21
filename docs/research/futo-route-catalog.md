# FUTO route catalog

The survey names 21 routes but does not contain geographic coordinates, route
lengths, or travel durations. The ML pipeline therefore requires a separate
route catalog before physical route features can be evaluated.

Generate a blank catalog template from the survey:

```powershell
uv run --extra ml python -m scripts.create_futo_route_catalog_template
```

This creates `data/external/futo_route_catalog.csv`. The file is intentionally
excluded from Git because external and derived data are ignored.

## Generate metadata candidates

The repository includes a helper that uses TomTom Geocoding and OSRM to create
reviewable candidates for the 21 FUTO routes:

```powershell
uv run --extra ml python -m scripts.generate_futo_route_catalog
```

Before running it, add a separate key with TomTom **Geocoding API** access to
the root `.env`:

```text
FUTO_GEOCODING_API_KEY=your-tomtom-geocoding-key
```

The existing traffic-flow key may not have geocoding access. The script makes
two geocoder requests per route, then requests OSRM distance and duration when
both endpoints resolve. It writes:

`data/external/futo_route_catalog_candidates.csv`

The candidate file contains the required catalog fields plus the original
queries, returned address matches, and notes. It never overwrites the raw
survey, includes API keys in output, or marks a generated row as verified.
TomTom's first match and OSRM's route are candidates only; inspect each route
against the actual FUTO case-study endpoints and correct them when necessary.

## Verified catalog fields

Copy accepted candidate values into `data/external/futo_route_catalog.csv` and
set `verification_status` to `verified` only after review. Every row must have:

- `origin_latitude`, `origin_longitude`
- `destination_latitude`, `destination_longitude`
- `distance_km`
- `duration_minutes`
- `source`
- `source_url`
- `verification_status`

Coordinates should represent the actual endpoints used for the FUTO case study.
Distances and durations must come from the cited routing source, with the route
profile, retrieval date, and requested time conditions recorded in the source
notes or research log. Do not estimate missing values from route names or insert
placeholder measurements into a training run.

After the catalog is complete and reviewed, run the physical-feature comparison:

```powershell
uv run --extra ml python -m scripts.train_futo_models --route-catalog data/external/futo_route_catalog.csv
```

The command validates that every survey route has complete, verified metadata
before training. Physical features are not connected to live fare estimation by
this experiment.