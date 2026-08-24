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

## Planned

- PostgreSQL integration tests against a managed or containerized database.
- Connect the external risk and demand adapters to verified, provenance-controlled
  data sources before enabling production fare estimation.
- Replace the in-process rate limiter and metrics registry with shared production
  backends when running more than one API replica.
- Add managed log/metric alerting, API-key rotation, and deployment load thresholds.
- Research dataset preparation and provenance-controlled ML experiments.
- Production map provider rendering and calibrated pricing coefficients.

## Research decisions required

- Empirical calibration of risk weights and pricing coefficients.
- Selection and validation of any production risk model.
- Availability and provenance of real route-risk and demand observations.

All values in the local simulation mode are placeholders and are labelled as
simulated; they are not research findings.
