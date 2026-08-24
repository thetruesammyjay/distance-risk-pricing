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
