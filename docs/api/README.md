# API documentation

The development OpenAPI document is available at `/docs` and `/redoc`. Public
routes are versioned under `/api/v1`; `/health` is intentionally unversioned.

The FUTO estimator loads its endpoint choices from the supplied coordinate
catalog. `GET /api/v1/locations` returns each endpoint's coordinates and source
metadata for the frontend selector.
