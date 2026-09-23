export type Coordinate = {
  latitude: number;
  longitude: number;
};

export type LocationOption = Coordinate & {
  location_id: string;
  endpoint_name: string;
  collected_at: string;
  source: string;
  source_url: string;
  notes: string;
};

export type FareRequest = {
  origin: Coordinate;
  destination: Coordinate;
  requested_at: string;
};

export type FareQuote = {
  quote_id: string;
  created_at: string;
  requested_at: string;
  origin: Coordinate;
  destination: Coordinate;
  route: {
    distance_km: number;
    estimated_duration_minutes: number;
    geometry: unknown;
    provider: string;
  };
  risk: {
    score: number;
    classification: 'Low' | 'Moderate' | 'High' | 'Very High';
    components: { accident: number | null; road: number | null; security: number | null; questionnaire: number | null };
    components_available: string[];
    components_missing: string[];
    weight_strategy: string;
    source_type: string;
    data_sources: string[];
    model_version: string;
  };
  demand: {
    requests: number;
    available_drivers: number;
    multiplier: number;
    source_type: string;
    data_sources: string[];
  };
  fare: {
    currency: string;
    base_fare: number;
    distance_component: number;
    risk_adjustment: number;
    demand_adjustment: number;
    total: number;
    formula_mode: 'additive' | 'multiplicative';
    formula_version: string;
    coefficient_version: string;
  };
  timings_ms: Record<string, number>;
};

export type ApiError = { error: { code: string; message: string; details?: unknown } };
