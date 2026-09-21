# Research data

Data flows from `raw/` to `interim/` to `processed/`. Original raw data must
remain untouched. `external/` is reserved for legitimate third-party data.

Do not add personally identifying data here. For every empirical or external
dataset, document provenance, licensing, acquisition date, preprocessing, and
known limitations.

## FUTO endpoint locations

`FUTO Route Endpoint Coordinate Collection.csv` is the runtime location catalog
for the FUTO estimator. It contains endpoint coordinates collected from Google
Maps, along with collection timestamps, source links, and notes. The API loads
this file and exposes it at `GET /api/v1/locations`; the frontend does not use
hard-coded coordinates or free-form mock locations.

Rows are preserved as supplied, including duplicate endpoint names. Each row is
assigned a stable row-based identifier so duplicate labels remain selectable and
traceable to their original source record.
