# Distance-Risk-Aware Dynamic Pricing Model for City Transportation Services

A web-based transportation pricing platform that calculates transparent and adaptive trip fares using **travel distance, route-level risk, and demand conditions**.

The system is designed as the implementation component of the research project:

> **Design and Implementation of a Distance-Risk-Aware Dynamic Pricing Model for City Transportation Services**

The project investigates how transportation pricing can move beyond conventional flat-rate and distance-only models by incorporating route-specific risk information and dynamic demand conditions into an explainable fare calculation.

**Repository:** `github.com/thetruesammyjay/distance-risk-pricing`

---

## Table of Contents

* [Overview](#overview)
* [Research Motivation](#research-motivation)
* [Problem Statement](#problem-statement)
* [Objectives](#objectives)
* [Core Features](#core-features)
* [System Architecture](#system-architecture)
* [Technology Stack](#technology-stack)
* [Monorepo Structure](#monorepo-structure)
* [System Components](#system-components)
* [Pricing Model](#pricing-model)
* [Route Risk Model](#route-risk-model)
* [Demand Model](#demand-model)
* [Risk Classification](#risk-classification)
* [Explainable Pricing](#explainable-pricing)
* [Machine Learning and Data Analysis](#machine-learning-and-data-analysis)
* [Data Pipeline](#data-pipeline)
* [Database Design](#database-design)
* [API Design](#api-design)
* [Example Fare Estimation](#example-fare-estimation)
* [Frontend](#frontend)
* [Backend](#backend)
* [Security](#security)
* [Performance and Caching](#performance-and-caching)
* [Getting Started](#getting-started)
* [Environment Variables](#environment-variables)
* [Database Setup](#database-setup)
* [Running the Project](#running-the-project)
* [Testing](#testing)
* [Deployment](#deployment)
* [Research Evaluation](#research-evaluation)
* [Limitations](#limitations)
* [Future Work](#future-work)
* [Development Principles](#development-principles)
* [Authors](#authors)
* [Academic Context](#academic-context)
* [License](#license)

---

## Overview

Traditional transportation pricing systems commonly determine fares using variables such as base fare, distance, travel duration, and demand. These approaches may fail to distinguish between two journeys of similar distance that expose drivers and passengers to substantially different operating conditions.

For example, two 10 km trips may differ because one route contains:

* poor road conditions
* historically accident-prone segments
* elevated security concerns
* congestion
* high-demand zones
* difficult operating conditions

The **Distance-Risk-Aware Dynamic Pricing System** introduces a route-risk component into transportation fare calculation.

```mermaid
flowchart TD
    A[Origin + Destination] --> B[Routing Layer]
    B -->|Distance + Route| C[Risk Intelligence]
    C -->|Risk Score| D[Demand Intelligence]
    D -->|Demand Multiplier| E[Pricing Engine]
    E --> F[Fare + Breakdown + Risk Explanation]
```

The final fare is influenced by:

```mermaid
flowchart LR
    A[Distance] --> D[Dynamic Fare]
    B[Route Risk] --> D
    C[Demand Conditions] --> D
```

The system also exposes the components used to calculate the fare so that the result is explainable rather than being presented as an unexplained final amount.

---

## Research Motivation

Ride-hailing and urban transportation platforms increasingly rely on algorithmic pricing. Many existing approaches focus primarily on:

* trip distance
* estimated travel duration
* current demand
* available drivers
* conventional surge multipliers

However, route-specific operating risks may also affect the practical cost of completing a journey, including accident exposure, poor road conditions, security concerns, difficult route segments, and time-dependent changes in perceived route risk.

The proposed system investigates whether route-level risk information can be incorporated into transportation pricing while maintaining transparency, computational efficiency, fairness, modularity, and auditability.

---

## Problem Statement

Conventional city transportation pricing models do not always account for the full range of conditions affecting a journey. A purely distance-based model may assign similar fares to routes of similar length despite major differences in operating conditions. Demand-based surge pricing partially addresses changing market conditions but may still ignore route-specific risks.

The proposed system addresses this problem by designing a pricing model that is:

1. **Distance-aware** — uses geospatial routing to determine the actual route distance
2. **Risk-aware** — associates transportation routes with measurable risk indicators
3. **Dynamic** — responds to changes in transportation demand
4. **Transparent** — provides a breakdown of the components contributing to the final fare
5. **Auditable** — stores relevant pricing inputs and outputs for later analysis

---

## Objectives

1. Develop a geospatial routing mechanism for estimating route distance and travel information.
2. Develop a route-risk assessment mechanism capable of producing a normalized Route Risk Coefficient.
3. Incorporate temporal route-risk information where appropriate data are available.
4. Develop a dynamic pricing algorithm combining distance, risk, and demand.
5. Implement an explainable fare breakdown showing how individual pricing components influence the final fare.
6. Develop a REST API through which the frontend communicates with the pricing system.
7. Build a web interface for requesting fare estimates and visualizing pricing information.
8. Store trip, risk, pricing, and audit information in a PostgreSQL database.
9. Evaluate the behaviour of the proposed pricing model using real, collected, derived, and/or simulated experimental data, with each data source clearly identified.

---

## Core Features

### Route-Based Fare Estimation

Users select an origin and destination and request an estimated fare. The system determines route, distance, estimated travel duration, route-risk score, demand conditions, and final estimated fare.

### Distance-Aware Pricing

Distance is obtained from a routing service rather than relying exclusively on straight-line geographic distance. Where configured, the backend can integrate with an OpenStreetMap-compatible routing engine such as OSRM.

### Route Risk Assessment

The system supports a composite Route Risk Coefficient based on available risk indicators:

```mermaid
flowchart LR
    A[Accident Risk] --> D[Route Risk Coefficient]
    B[Road Condition Risk] --> D
    C[Security Risk] --> D
```

Only risk components backed by available or explicitly simulated data should be enabled in experimental results.

### Time-Aware Security Risk

Where questionnaire or historical observations contain risk assessments across different periods, security risk can vary according to both route and time period:

```text
SecurityRisk = f(Route, Time)
```

This allows the same route to have different risk estimates at different times.

### Dynamic Demand Adjustment

The pricing model supports adjustment based on demand and supply conditions. A configurable upper limit prevents uncontrolled demand multipliers.

### Explainable Fare Breakdown

Instead of returning only a final amount, the system exposes contributing components: base fare, distance cost, route risk adjustment, demand adjustment, and final fare.

### Risk Visualization

The frontend can visualize route risk, risk category, route-time risk, fare components, demand multiplier, and estimated route.

### Audit Logging

Fare calculations can be recorded alongside their inputs, allowing the pricing process to be inspected and reproduced.

---

## System Architecture

The application uses a web-based service-oriented architecture.

```mermaid
flowchart TD
    Internet((Internet)) --> FE["Next.js Frontend (Vercel)"]
    FE -->|HTTPS| GW["API Gateway (FastAPI)"]
    GW --> PE[Pricing Engine]
    PE --> RS[Routing Service]
    PE --> RK[Risk Service]
    PE --> DS[Demand Service]
    RS --> OSM[(Routing / OSM)]
    RK --> DB[(Neon PostgreSQL)]
    DS --> DemandStore[(Demand Store)]
    DemandStore --> DB
```

The services are logically separated by domain responsibility. For the initial deployment, they may run within a manageable number of backend processes rather than requiring a complex container orchestration platform.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Frontend Language | TypeScript |
| UI | React |
| Styling | Tailwind CSS |
| Backend | FastAPI |
| Backend Language | Python |
| API | REST / OpenAPI |
| Database | Neon PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Database Migrations | Alembic |
| Routing | OpenStreetMap / OSRM-compatible routing |
| Geographic Indexing | H3 where required |
| Data Processing | Pandas / NumPy |
| Machine Learning | Scikit-learn |
| Advanced ML | XGBoost / CatBoost where justified |
| Explainability | SHAP |
| Backend Testing | Pytest |
| Frontend Testing | Vitest / Playwright |
| Frontend Hosting | Vercel |
| Backend Hosting | Render |
| Source Control | Git / GitHub |
| CI/CD | GitHub Actions |

---

## Monorepo Structure

```text
distance-risk-pricing/
├── apps/
│   └── web/
│       ├── public/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── features/
│       │   ├── hooks/
│       │   ├── lib/
│       │   ├── services/
│       │   ├── types/
│       │   └── utils/
│       ├── package.json
│       └── README.md
│
├── services/
│   ├── api-gateway/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   ├── schemas/
│   │   │   └── config/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── pricing-engine/
│   │   ├── app/
│   │   │   ├── engine/
│   │   │   │   ├── pricing.py
│   │   │   │   ├── coefficients.py
│   │   │   │   ├── breakdown.py
│   │   │   │   └── validators.py
│   │   │   ├── schemas/
│   │   │   └── config/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── routing-service/
│   │   ├── app/
│   │   │   ├── clients/
│   │   │   ├── routing/
│   │   │   ├── cache/
│   │   │   └── schemas/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── risk-service/
│   │   ├── app/
│   │   │   ├── risk/
│   │   │   │   ├── accident.py
│   │   │   │   ├── road_quality.py
│   │   │   │   ├── security.py
│   │   │   │   ├── normalization.py
│   │   │   │   └── aggregator.py
│   │   │   ├── repositories/
│   │   │   └── schemas/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── demand-service/
│       ├── app/
│       │   ├── demand/
│       │   │   ├── multiplier.py
│       │   │   ├── zone_stats.py
│       │   │   └── h3_index.py
│       │   ├── repositories/
│       │   └── schemas/
│       ├── tests/
│       └── pyproject.toml
│
├── ml/
│   ├── notebooks/
│   │   ├── 01_data_audit.ipynb
│   │   ├── 02_eda.ipynb
│   │   ├── 03_risk_modelling.ipynb
│   │   └── 04_model_evaluation.ipynb
│   ├── src/
│   │   ├── preprocessing/
│   │   ├── feature_engineering/
│   │   ├── training/
│   │   ├── evaluation/
│   │   ├── explainability/
│   │   └── inference/
│   ├── models/
│   └── tests/
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   ├── external/
│   └── README.md
│
├── packages/
│   ├── shared-python/
│   ├── shared-types/
│   └── pricing-contracts/
│
├── database/
│   ├── migrations/
│   ├── seeds/
│   ├── schema/
│   └── README.md
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── research/
│   └── diagrams/
│
├── scripts/
│   ├── preprocess_data.py
│   ├── seed_database.py
│   ├── train_models.py
│   ├── evaluate_models.py
│   └── generate_reports.py
│
├── tests/
│   ├── integration/
│   ├── e2e/
│   └── performance/
│
├── .github/
│   └── workflows/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── render.yaml
├── Makefile
├── README.md
└── LICENSE
```

---

## System Components

### 1. Web Application

Location: `apps/web/`

Responsibilities: selecting trip origin and destination, displaying routes, requesting fare estimates, displaying distance, risk classification, and demand information, showing the estimated fare, explaining the fare breakdown, and visualizing relevant route information.

The web application communicates only with the public backend API and should not communicate directly with internal pricing services or the database.

### 2. API Gateway

Location: `services/api-gateway/`

Responsibilities: HTTP request handling, validation, authentication where required, rate limiting, CORS, API versioning, exception handling, request tracing, and communication with the pricing domain.

Example public endpoint:

```http
POST /api/v1/fares/estimate
```

### 3. Routing Service

Location: `services/routing-service/`

The Routing Service determines the route between an origin and destination.

```mermaid
flowchart TD
    A[Origin] --> B[Road Network]
    B --> C[Routing Algorithm]
    C --> D[Optimal Route]
    D --> E[Distance]
    D --> F[Duration]
    D --> G[Route Geometry]
```

Inputs: origin coordinates, destination coordinates.
Outputs: route geometry, distance, estimated duration, route/segment information.

### 4. Risk Assessment Service

Location: `services/risk-service/`

The Risk Assessment Service determines the risk associated with a route, considering three major dimensions:

```text
R_acc  = Accident Risk
R_road = Road Condition Risk
R_sec  = Security Risk
```

These are normalized before aggregation. The service must distinguish between observed risk data, questionnaire-derived perception data, externally sourced data, and simulated data. The system must never silently represent simulated risk information as observed real-world risk.

### 5. Demand Intelligence Service

Location: `services/demand-service/`

The Demand Intelligence Service estimates transportation demand conditions within a geographic area, using the ratio of active requests to available drivers to determine demand-supply pressure.

For prototype experiments where real ride-hailing demand data are unavailable, demand scenarios may be simulated. Any simulated demand must be explicitly labelled as simulated.

### 6. Pricing Engine

Location: `services/pricing-engine/`

The Pricing Engine is the core domain component. It receives distance, risk, demand, and pricing configuration, and produces a fare, fare breakdown, and pricing metadata. The Pricing Engine should contain pure, independently testable pricing logic wherever possible.

---

## Pricing Model

The original proposed pricing function is:

```text
F = B + (α × D) + (β × D × R) + (γ × M)
```

| Symbol | Meaning |
|---|---|
| F | Final fare |
| B | Base fare |
| D | Trip distance |
| R | Route Risk Coefficient |
| M | Demand factor |
| α | Distance-rate coefficient |
| β | Risk-premium coefficient |
| γ | Demand-sensitivity coefficient |

Before empirical evaluation, the implementation should explicitly define whether `M` is treated as an additive demand term or as a true multiplier. A multiplicative formulation may instead be expressed as:

```text
F = [B + (α × D) + (β × D × R)] × M
```

The selected formulation must remain consistent across source code, API documentation, experiments, dissertation/seminar documentation, user interface, and research results.

---

## Route Risk Model

The proposed Route Risk Coefficient is:

```text
R = (w1 × R_acc) + (w2 × R_road) + (w3 × R_sec)
```

subject to:

```text
w1 + w2 + w3 = 1
0 <= R <= 1
```

* **Accident Risk (R_acc)** — normalized accident exposure
* **Road Risk (R_road)** — road-condition-related operating risk; higher values represent poorer or more difficult road conditions
* **Security Risk (R_sec)** — available security-risk information. Where perception questionnaires are used, this must be described as a **perceived security-risk measure**, not verified crime probability

---

## Demand Model

The proposed demand multiplier is:

```text
M = min(1 + λ × (Req / Sup - 1), M_cap)
```

| Variable | Description |
|---|---|
| Req | Active trip requests |
| Sup | Available drivers |
| λ | Demand sensitivity |
| M_cap | Maximum permitted multiplier |

The implementation should enforce `M >= 1.0`, therefore:

```text
if Req / Sup <= 1:
    M = 1.0
```

The demand multiplier cap prevents excessive fare escalation.

---

## Risk Classification

Normalized route risk can be mapped into human-readable categories:

| Score | Classification |
|---|---|
| 0.00 – 0.25 | Low |
| 0.26 – 0.50 | Moderate |
| 0.51 – 0.75 | High |
| 0.76 – 1.00 | Very High |

These thresholds are configurable and should not automatically be interpreted as externally validated safety thresholds. They are primarily system-level classification bands unless empirical validation establishes otherwise.

---

## Explainable Pricing

Transparency is a major design requirement. The system should not return only a final price. For example:

```text
Estimated Fare

Base Fare                 ₦500
Distance Component      ₦1,920
Route Risk Adjustment     ₦585
Demand Adjustment         ₦901
--------------------------------
Estimated Total         ₦3,906
```

The interface may additionally display:

```text
Distance:           12.8 km
Estimated Duration: 31 minutes
Route Risk:         High
Risk Score:         0.61
Demand Multiplier:  1.35x
```

The purpose is to make the algorithm's output understandable and auditable.

---

## Machine Learning and Data Analysis

Machine learning is treated as a supporting component of the risk-intelligence layer rather than the entire pricing system.

```mermaid
flowchart TD
    A[Collected Dataset] --> B[Data Cleaning]
    B --> C[Long-Format Transformation]
    C --> D[Exploratory Analysis]
    D --> E[Feature Engineering]
    E --> F[Model Training]
    F --> G[Validation]
    G --> H[Risk Model]
    H --> I[Risk Service]
    I --> J[Pricing Engine]
```

Potential models: Logistic Regression, Ordinal Logistic Regression, Decision Tree, Random Forest, Extra Trees, Support Vector Machine, XGBoost, CatBoost. Models should only be retained where they improve the research or implementation — a complex model should not be selected simply because it is more sophisticated.

### Leakage Prevention

Where individual respondents provide multiple route/time ratings, observations from the same respondent should not be distributed arbitrarily across training and validation sets. Grouped validation should therefore be considered using respondent identifiers, e.g. `GroupKFold`, `StratifiedGroupKFold`, `GroupShuffleSplit`. This prevents the model from being evaluated against observations from respondents whose other responses were already observed during training.

---

## Data Pipeline

The data directories follow a staged processing strategy.

```mermaid
flowchart LR
    A["data/raw/"] --> B["data/interim/"]
    B --> C["data/processed/"]
    C --> D[Model Training]
    D --> E[Validated Model]
    E --> F[Risk Service]
```

**Raw Data** (`data/raw/`) — contains untouched source data; raw data should never be overwritten.

**Interim Data** (`data/interim/`) — cleaned records, normalized categories, reshaped observations, intermediate transformations.

**Processed Data** (`data/processed/`) — analysis-ready datasets, e.g. `route_time_risk.csv`, `security_risk_index.csv`, `model_features.csv`.

**External Data** (`data/external/`) — reserved for legitimate third-party data such as road network data, accident records, road-condition data, and geographic information. The provenance of external data should be documented.

---

## Database Design

The production database uses **Neon PostgreSQL**.

Core entities may include: `users`, `trips`, `trip_routes`, `route_segments`, `risk_segments`, `risk_observations`, `risk_predictions`, `zones`, `zone_demand`, `pricing_coefficients`, `fare_quotes`, `fare_breakdowns`, `model_versions`, `audit_logs`.

```mermaid
erDiagram
    USER ||--o{ TRIP : requests
    TRIP ||--|| TRIP_ROUTE : has
    TRIP_ROUTE ||--o{ ROUTE_SEGMENT : contains
    ROUTE_SEGMENT ||--o{ RISK_SEGMENT : "assessed for"
    TRIP ||--|| FARE_QUOTE : produces
    FARE_QUOTE ||--|| FARE_BREAKDOWN : includes
    FARE_QUOTE ||--|| PRICING_COEFFICIENTS : uses
    FARE_QUOTE ||--|| RISK_PREDICTION : uses
    FARE_QUOTE ||--|| DEMAND_SNAPSHOT : uses
```

---

## API Design

The public API follows REST principles.

Base path: `/api/v1`

Potential endpoints:

```http
GET  /health
GET  /api/v1/config
POST /api/v1/routes/estimate
POST /api/v1/risk/estimate
POST /api/v1/fares/estimate
GET  /api/v1/fares/{quote_id}
GET  /api/v1/risk/routes/{route_id}
```

### Fare Estimate

```http
POST /api/v1/fares/estimate
```

Example request:

```json
{
  "origin": {
    "latitude": 5.3921,
    "longitude": 7.0337
  },
  "destination": {
    "latitude": 5.4865,
    "longitude": 7.0259
  },
  "requested_at": "2026-08-23T18:30:00"
}
```

Example response:

```json
{
  "quote_id": "quote_01",
  "route": {
    "distance_km": 12.8,
    "estimated_duration_minutes": 31
  },
  "risk": {
    "score": 0.61,
    "classification": "High"
  },
  "demand": {
    "multiplier": 1.35
  },
  "fare": {
    "currency": "NGN",
    "base": 500,
    "distance_component": 1920,
    "risk_adjustment": 585,
    "demand_adjustment": 901,
    "total": 3906
  }
}
```

The exact numerical values above are illustrative API examples and must not be represented as experimental research results.

---

## Example Fare Estimation

Consider a hypothetical journey with:

```text
Distance = 12.8 km
Risk Score = 0.61
Demand Multiplier = 1.35
```

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant RS as Routing Service
    participant RK as Risk Service
    participant DS as Demand Service
    participant PE as Pricing Engine

    U->>GW: Request fare (origin, destination)
    GW->>RS: Get route
    RS-->>GW: 12.8 km
    GW->>RK: Get route risk
    RK-->>GW: Risk = 0.61
    GW->>DS: Get demand
    DS-->>GW: M = 1.35
    GW->>PE: Compute fare (D, R, M)
    PE-->>GW: Explainable fare
    GW-->>U: Fare + breakdown
```

All numerical values in this example are illustrative until derived from the implemented system or experimental dataset.

---

## Frontend

Located at `apps/web/`, built with Next.js, TypeScript, React, and Tailwind CSS.

Suggested pages:

```text
/
├── /
├── /estimate
├── /quote/[id]
├── /risk
├── /methodology
└── /about
```

Potential UI components: `Map`, `LocationSearch`, `RoutePreview`, `FareEstimator`, `FareBreakdown`, `RiskIndicator`, `DemandIndicator`, `RiskExplanation`, `QuoteSummary`.

---

## Backend

The backend is implemented in Python using FastAPI, which provides request validation, asynchronous HTTP handling, OpenAPI generation, interactive API documentation, dependency injection, and typed request/response schemas.

Backend API documentation is available during development through `/docs` and `/redoc`.

---

## Security

The system should apply standard web API security practices, including:

* HTTPS in production
* CORS restrictions
* environment-variable-based secret management
* request validation
* SQL injection protection through parameterized ORM queries
* rate limiting where appropriate
* secure database connections
* sanitized error responses
* dependency updates
* audit logging

Sensitive values must never be committed to GitHub, including `.env`, `DATABASE_URL`, API keys, private credentials, and service tokens.

---

## Performance and Caching

Route computation and repeated geographic lookups can be expensive. Caching may be introduced for frequently requested routes, risk lookups, demand snapshots, and configuration values. A cache is an optimization rather than the primary source of truth — the authoritative persistent data remain in PostgreSQL.

---

## Getting Started

### Prerequisites

```text
Git
Node.js
npm/pnpm
Python 3.11+
PostgreSQL client tools, optional
```

Clone the repository:

```bash
git clone https://github.com/thetruesammyjay/distance-risk-pricing.git
cd distance-risk-pricing
```

---

## Environment Variables

Create local environment files from the supplied examples.

### Backend

```env
APP_ENV=development
APP_NAME=distance-risk-pricing
DEBUG=true

DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require

FRONTEND_URL=http://localhost:3000

ROUTING_BASE_URL=https://router.project-osrm.org

PRICING_BASE_FARE=500
PRICING_DISTANCE_RATE=150
PRICING_RISK_WEIGHT=0.30
PRICING_DEMAND_CAP=2.5

LOG_LEVEL=INFO
```

The pricing values above are examples only. Final coefficients should be configured from the selected experimental/calibration results.

### Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:

```env
NEXT_PUBLIC_API_URL=<RENDER_BACKEND_URL>
```

---

## Database Setup

The application uses Neon PostgreSQL. After creating the Neon database, configure:

```env
DATABASE_URL=<NEON_DATABASE_CONNECTION_STRING>
```

Apply migrations:

```bash
alembic upgrade head
```

Optionally seed development data:

```bash
python scripts/seed_database.py
```

Never commit the Neon database password or complete private connection string.

---

## Running the Project

### Backend

```bash
uv sync --dev

uv run uvicorn services.api_gateway.app.main:app --reload
```

The backend becomes available at `http://localhost:8000`, with interactive API documentation at `http://localhost:8000/docs`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Testing

Testing is divided into several levels.

### Unit Tests

Test individual components: risk normalization, risk aggregation, demand multiplier, pricing calculation, fare breakdown, input validation.

```bash
pytest
```

### Integration Tests

Validate interactions such as API → Pricing Engine, Pricing Engine → Routing/Risk/Demand Services, and Backend → Neon PostgreSQL.

### End-to-End Tests

```mermaid
flowchart LR
    A[Select Origin] --> B[Select Destination]
    B --> C[Request Fare]
    C --> D[Route Calculated]
    D --> E[Risk Calculated]
    E --> F[Demand Calculated]
    F --> G[Fare Generated]
    G --> H[Breakdown Displayed]
```

---

## Deployment

The project uses separate frontend and backend deployments.

```mermaid
flowchart TD
    GH[GitHub] --> V[Vercel — Frontend]
    GH --> R[Render — Backend]
    V --> DB[(Neon PostgreSQL)]
    R --> DB
```

### Frontend Deployment — Vercel

Configure the frontend root directory as `apps/web`. Set:

```env
NEXT_PUBLIC_API_URL=<RENDER_BACKEND_URL>
```

The production frontend must communicate with the backend over HTTPS.

### Backend Deployment — Render

Typical start command:

```bash
uv run uvicorn services.api_gateway.app.main:app --host 0.0.0.0 --port $PORT
```

Production environment variables should include `DATABASE_URL`, `FRONTEND_URL`, `ROUTING_BASE_URL`, pricing configuration, and other required service credentials. Secrets must be configured through Render's environment management rather than committed to Git.

### Database Deployment — Neon

Neon provides managed PostgreSQL infrastructure. The backend communicates directly with Neon over a secure PostgreSQL connection; the browser should never connect directly to the production database.

---

## Research Evaluation

The implemented system should be evaluated at both the model and software levels.

### Risk Evaluation

Where predictive modelling is used, potential metrics include Accuracy, Balanced Accuracy, Macro F1, Weighted F1, Cohen's Kappa, Matthews Correlation Coefficient, Quadratic Weighted Kappa, and ordinal error.

### Pricing Evaluation

Pricing experiments should investigate the effect of distance, route risk, and demand on fare; sensitivity to coefficient changes; price-cap behaviour; stability; and transparency.

### System Evaluation

Software evaluation may measure API response time, routing latency, risk-calculation latency, pricing-calculation latency, database query performance, end-to-end fare estimation time, and error rate under test load.

### Baseline Comparison

| Model | Description |
|---|---|
| A | Distance-Only Pricing |
| B | Distance + Demand Pricing |
| C | Distance + Risk Pricing |
| D | Distance + Risk + Demand Pricing |

This allows the contribution of each component to be studied independently. The evaluation must not assume that Model D is superior before experiments are conducted.

---

## Limitations

**Data Availability** — Reliable fine-grained accident, road-condition, security incident, and ride demand data may not be consistently available.

**Perception vs Actual Risk** — Questionnaire-derived route-risk assessments measure perceived risk. They should not automatically be interpreted as actual crime probability or actual accident probability.

**Demand Simulation** — If real ride-hailing demand information is unavailable, demand experiments may require simulated scenarios, which must be clearly identified as simulations.

**Model Calibration** — Pricing coefficients require empirical calibration. Prototype coefficients should not be presented as universally optimal transportation prices.

**Geographic Generalization** — Results obtained from one study environment may not generalize directly to other Nigerian cities.

**External API Dependency** — Routing performance may depend on the availability and accuracy of third-party mapping infrastructure.

---

## Future Work

1. Real-time traffic integration
2. Weather-aware risk estimation
3. Fuel-price-aware pricing
4. Verified accident-data integration
5. Verified security-incident integration
6. Improved road-quality datasets
7. Real ride-hailing demand feeds
8. Reinforcement-learning-based demand optimization
9. Advanced spatial risk modelling
10. Real-time driver availability
11. Alternative-route recommendation
12. Fairness-aware pricing constraints
13. Regulatory pricing dashboards
14. Multi-modal transportation support
15. Shared-ride pricing
16. External validation across multiple Nigerian cities

---

## Development Principles

**No Fabricated Data** — Missing information must not be silently invented.

**No Fabricated Risk Claims** — A route must not be described as objectively dangerous solely because questionnaire respondents perceived it as risky.

**No Fabricated Performance** — Model metrics must come from actual experiments.

**Reproducibility** — Experiments should record dataset version, preprocessing, features, model, parameters, validation strategy, random seed, and evaluation metrics.

**Explainability** — Fare calculations should be decomposable and inspectable.

**Separation of Concerns**

```text
Routing != Risk Assessment
Risk Assessment != Pricing
Pricing != Frontend
Research Training != Production Inference
```

Each component has a clearly defined responsibility.

---

## Authors

**Chukwudifu Golden Ifeanyichukwu** — Registration Number: `20211258722`

**Obikudu Chigozie Jeffrey** — Registration Number: `20222314712`

---

## Academic Context

This repository supports the implementation and evaluation of the project:

> **Design and Implementation of a Distance-Risk-Aware Dynamic Pricing Model for City Transportation Services**

Submitted to:

**Department of Software Engineering**
**School of Information and Communication Technology**
**Federal University of Technology Owerri**

In partial fulfillment of the requirements for the award of **Bachelor of Technology (B.Tech) in Software Engineering**.

---

## Repository

`github.com/thetruesammyjay/distance-risk-pricing`

---

## Disclaimer

This project is an academic research prototype. Risk scores, route classifications, and fare estimates produced by the system should not be interpreted as guarantees of personal safety, predictions of criminal activity, official transportation tariffs, or authoritative assessments of road safety.

Where simulated, questionnaire-derived, or experimental data are used, the source and nature of those data should be clearly identified.

---

## License

This project is intended primarily for academic and research purposes. A formal open-source license may be added depending on the intended distribution and reuse requirements.
