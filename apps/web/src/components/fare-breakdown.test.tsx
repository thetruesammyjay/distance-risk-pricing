import { render, screen } from '@testing-library/react';
import { FareBreakdown } from './fare-breakdown';

const quote = {
  quote_id: 'quote',
  created_at: '',
  requested_at: '',
  origin: { latitude: 1, longitude: 1 },
  destination: { latitude: 2, longitude: 2 },
  route: { distance_km: 10, estimated_duration_minutes: 20, geometry: null, provider: 'test' },
  risk: {
    score: 0.6,
    classification: 'High' as const,
    components: { accident: 0.4, road: 0.5, security: 0.6 },
    components_available: ['accident'],
    components_missing: [],
    weight_strategy: 'configured_components',
    source_type: 'simulated',
    data_sources: ['simulated'],
    model_version: 'v1',
  },
  demand: {
    requests: 1,
    available_drivers: 1,
    multiplier: 1,
    source_type: 'simulated',
    data_sources: ['simulated'],
  },
  fare: {
    currency: 'NGN',
    base_fare: 1500,
    distance_component: 0,
    risk_adjustment: 6,
    demand_adjustment: 1,
    total: 2007,
    formula_mode: 'additive' as const,
    formula_version: 'v2-distance-base',
    coefficient_version: 'prototype-v1',
  },
  timings_ms: { routing: 1, risk: 1, demand: 1, pricing: 1, database_persistence: 1 },
};

test('renders an explainable fare breakdown', () => {
  render(<FareBreakdown quote={quote} />);
  expect(screen.getByText(/estimated fare/i)).toBeInTheDocument();
  expect(screen.getByText(/distance-adjusted base fare/i)).toBeInTheDocument();
});
