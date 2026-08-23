# Implementation status

## Completed in this scaffold

- Monorepo directories and local development configuration.
- FastAPI health endpoint, request IDs, CORS, validation, and error envelope.
- Deterministic pricing, risk classification, and demand multiplier modules.
- OSRM adapter boundary and explicitly labelled simulated risk/demand modes.
- SQLAlchemy models, Alembic initial migration, and in-memory development repository.
- Next.js pages for the documented MVP routes.
- Backend unit/API test foundation and GitHub Actions workflow.

## Planned

- PostgreSQL integration tests against a managed or containerized database.
- Research dataset preparation and provenance-controlled ML experiments.
- Production map provider rendering and calibrated pricing coefficients.

## Research decisions required

- Empirical calibration of risk weights and pricing coefficients.
- Selection and validation of any production risk model.
- Availability and provenance of real route-risk and demand observations.

All values in the local simulation mode are placeholders and are labelled as
simulated; they are not research findings.

