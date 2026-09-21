# Implementation status

## Completed in this scaffold

- Monorepo directories and local development configuration.
- FastAPI health endpoint, request IDs, CORS, validation, and error envelope.
- Deterministic pricing, risk classification, and demand multiplier modules.
- OSRM adapter boundary and explicitly labelled simulated risk/demand modes.
- SQLAlchemy models, Alembic initial migration, and in-memory development repository.
- Next.js pages for the documented MVP routes.
- Backend unit/API test foundation and GitHub Actions workflow.
- Provider interfaces, pooled routing HTTP, bounded retries, sanitized API errors,
  production configuration guards, and exact PostgreSQL numeric persistence.
- Separate liveness (`/health`) and dependency readiness (`/ready`) endpoints.
- Prometheus-compatible request counters and duration metrics at `/metrics`.
- Optional API-key authentication, security headers, request IDs, and bounded
  per-process sliding-window rate limiting.
- Configurable asynchronous HTTP adapters for external risk and demand providers,
  with response validation and bounded retries.
- Deployment and load smoke scripts under `scripts/`.
- Stage-level fare timings, bounded OSRM TTL caching with request coalescing, and fare-endpoint load smoke testing.
- Verified Open-Meteo weather-risk and deterministic time-of-day demand simulation modes with provenance labels.
- Added the supplied FUTO endpoint coordinate catalog, a provenance-preserving `/api/v1/locations` endpoint, and dataset-backed frontend endpoint selection.

- Added the initial ML research pipeline: validated records, provenance-aware CSV preprocessing, leakage-safe feature engineering, respondent-grouped splitting, and classification evaluation metrics.

- Prepared the FUTO Google Forms export and ran grouped baseline model comparisons with reproducible JSON reporting.

- Added FUTO route/time ablations, class-balanced baseline comparisons, per-class recall, and fold confusion matrices.

## Planned

- PostgreSQL integration tests against a managed or containerized database.
- Compare the time-of-day demand scenario and external Open-Meteo signal against local observations.
- Connect an empirically calibrated route-risk dataset before enabling production fare estimation.
- Replace the in-process rate limiter and metrics registry with shared production
  backends when running more than one API replica.
- Add managed log/metric alerting, API-key rotation, and deployment load thresholds.

- Production map provider rendering and calibrated pricing coefficients.

## Research decisions required

- Empirical calibration of risk weights and pricing coefficients.
- Selection and validation of any production risk model.
- Availability and provenance of real route-risk and demand observations.

All values in the local simulation mode are placeholders and are labelled as
simulated; they are not research findings.
