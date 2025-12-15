// Simplified types for the planner map view
export type TimeHorizon = '1d' | '2d' | '3d';
export type RuleScenario = 'best' | 'normal' | 'worst';

export const RULE_SCENARIO_LABELS: Record<RuleScenario, string> = {
  best: 'Best',
  normal: 'Normal',
  worst: 'Worst',
};

export interface ZoneProperties {
  id: string;
  name: string;
  population: number;
  critical_assets: string[];
  admin_level: number;
}

export interface GeoJSON {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    properties: ZoneProperties;
    geometry: {
      type: 'Polygon';
      coordinates: number[][][];
    };
  }[];
}

export interface RiskDriver {
  feature: string;
  contribution: number;
}

export interface RiskPoint {
  zoneId: string;
  risk: number;
  drivers: RiskDriver[];
  thresholdBand: string;
  etaHours: number;
}

export interface Alert {
  id: string;
  zoneId: string;
  title: string;
  severity: 'Severe' | 'Moderate' | 'Low';
  message: string;
  timestamp: string;
}

export interface PipelineRuleBasedAllocation {
  zone_id: string;
  units_allocated: number;
  impact_level: string;
  allocation_mode: string;
  pf?: number;
  vulnerability?: number;
}

// Backend API types
export interface BackendForecast {
  median: number | null;
  xgboost: number | null;
  bayesian: number | null;
  lstm: number | null;
}

export interface BackendInterval {
  lower: number;
  upper: number;
  width: number;
  median?: number;
}

export interface BackendPrediction {
  lead_time_days: number;
  forecast_date: string;
  forecast: BackendForecast | null;
  prediction_interval_80pct?: BackendInterval | null;
  conformal_interval_80pct?: BackendInterval | null;
  flood_risk: {
    probability: number | null;
    threshold_ft: number;
    risk_level: string | null;
    risk_indicator: string | null;
  } | null;
  error?: string;
}

export interface BackendPredictResponse {
  timestamp: string;
  use_real_time_api: boolean;
  data_source: string;
  predictions: BackendPrediction[];
}

export interface RawDataRow {
  date: string;
  daily_precip: number;
  daily_temp_avg: number;
  daily_snowfall: number;
  daily_humidity: number;
  daily_wind: number;
  soil_deep_30d: number;
  target_level_max: number;
  hermann_level: number;
  grafton_level: number;
}

export interface PredictionHistoryItem {
  date: string;
  predicted_level: number | null;
  flood_probability: number | null;
  days_ahead: number;
  created_at: string;
  lower_bound_80?: number | null;
  upper_bound_80?: number | null;
}

export interface ZoneRow {
  zone_id: string;
  name: string;
  river_proximity: number;
  elevation_risk: number;
  pop_density: number;
  crit_infra_score: number;
  hospital_count: number;
  critical_infra: boolean;
}

export interface GaugePoint {
  id: string;
  name: string;
  lat: number;
  lon: number;
  usgs_id: string;
}

export interface GeoFeature {
  type: 'Feature';
  geometry: any;
  properties: Record<string, any>;
}

export interface GeoFeatureCollection {
  type: 'FeatureCollection';
  features: GeoFeature[];
}
