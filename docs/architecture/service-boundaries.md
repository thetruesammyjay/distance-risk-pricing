# Service boundary rules

The API gateway is the only browser-facing service. It orchestrates the
following in-process boundaries:

```text
API gateway → RoutingService → RoutingProvider
            → RiskService    → RiskProvider
            → DemandService  → DemandProvider
            → Pricing engine
            → FareQuoteRepository
```

Provider adapters own external I/O. Domain services own validation and
business rules. The simulated providers are deterministic development
implementations and identify their source as `simulated`; they are not
silently selected for production. Unsupported real-data modes return explicit
availability errors until a real adapter is configured.

Production requires `DATABASE_URL`, disallows wildcard CORS, uses pooled
database connections, stores monetary values as PostgreSQL `NUMERIC`, and
returns sanitized error envelopes without stack traces.

