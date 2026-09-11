# External provider contracts

The gateway supports external providers through small HTTP contracts. These
adapters are deliberately provider-neutral until a validated vendor or
research data source is selected.

## Risk provider

`POST RISK_PROVIDER_URL` receives:

```json
{
  "origin": {"latitude": 5.3921, "longitude": 7.0337},
  "destination": {"latitude": 5.4865, "longitude": 7.0259},
  "requested_at": "2026-08-23T18:30:00+01:00"
}
```

It must return `components.accident`, `components.road`, and
`components.security` as values between 0 and 1 or `null`, plus a non-empty
`data_sources` array. `source_type` should be `external` and
`model_version` must identify the deployed model.

## Demand provider

`GET DEMAND_PROVIDER_URL` must return:

```json
{
  "requests": 120,
  "available_drivers": 40,
  "source_type": "external"
}
```

Both adapters send `Authorization: Bearer <provider-api-key>` when a provider
API key is configured. Responses are retried for transient failures and are
rejected when their shape or values are invalid.

## Verified external source modes

The prototype includes two concrete adapters:

- `RISK_MODE=open_meteo` calls the Open-Meteo Forecast API at `RISK_PROVIDER_URL`. It derives one weather-based road-condition component from precipitation, wind gusts, visibility, and WMO weather code. Accident and security remain missing and are not inferred.
- `DEMAND_MODE=tomtom_traffic` calls TomTom Traffic Flow Segment Data at `DEMAND_PROVIDER_URL`. It uses observed speed versus free-flow speed as a demand-pressure proxy; it does not claim to measure ride requests or driver availability. Configure the TomTom credential as `DEMAND_PROVIDER_API_KEY`.

Both sources are recorded in quote provenance and should be evaluated against local observations before being used in research conclusions or production pricing.