import { z } from "zod";

// Core enums
export const RiskBandSchema = z.enum(["Low", "Moderate", "High", "Severe"]);
export const RoleSchema = z.enum(["Administrator", "Planner", "Coordinator", "Data Analyst"]);
export const CrewStatusSchema = z.enum(["ready", "enroute", "working", "rest"]);
export const EquipmentStatusSchema = z.enum(["available", "deployed", "maintenance"]);
export const AlertSeveritySchema = z.enum(["Low", "Moderate", "High", "Severe", "Operational"]);
export const AlertTypeSchema = z.enum(["System", "Crew"]);
export const AlertStatusSchema = z.enum(["open", "acknowledged", "resolved"]);
export const TrendSchema = z.enum(["rising", "steady", "falling"]);

// Risk and forecasting
export const RiskDriverSchema = z.object({
  feature: z.string(),
  contribution: z.number().min(0).max(1),
});

export const RiskPointSchema = z.object({
  zoneId: z.string(),
  risk: z.number().min(0).max(1),
  drivers: z.array(RiskDriverSchema),
  thresholdBand: RiskBandSchema,
  etaHours: z.number().int().nonnegative(),
});

export const DamageIndexSchema = z.object({
  zoneId: z.string(),
  infra_index: z.number().min(0).max(1),
  human_index: z.number().min(0).max(1),
  notes: z.array(z.string()),
});

// Geographic data
export const ZonePropertiesSchema = z.object({
  id: z.string(),
  name: z.string(),
  population: z.number().int().positive(),
  critical_assets: z.array(z.string()),
  admin_level: z.number().int().positive(),
});

export const GeoJSONFeatureSchema = z.object({
  type: z.literal("Feature"),
  properties: ZonePropertiesSchema,
  geometry: z.object({
    type: z.literal("Polygon"),
    coordinates: z.array(z.array(z.array(z.number()))),
  }),
});

export const GeoJSONSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(GeoJSONFeatureSchema),
});

// Resources
export const DepotSchema = z.object({
  id: z.string(),
  name: z.string(),
  lat: z.number(),
  lng: z.number(),
});

export const EquipmentSchema = z.object({
  id: z.string(),
  type: z.string(),
  subtype: z.string().optional(),
  capacity_lps: z.number().optional(),
  units: z.number().optional(),
  depot: z.string(),
  status: EquipmentStatusSchema,
});

export const CrewSchema = z.object({
  id: z.string(),
  name: z.string(),
  skills: z.array(z.string()),
  depot: z.string(),
  status: CrewStatusSchema,
  lat: z.number(),
  lng: z.number(),
});

export const ResourcesSchema = z.object({
  depots: z.array(DepotSchema),
  equipment: z.array(EquipmentSchema),
  crews: z.array(CrewSchema),
});

// Planning and assignments
export const ActionSchema = z.object({
  type: z.string(),
  qty: z.number().optional(),
  from: z.string().optional(),
  equipment: z.string().optional(),
  crew: z.string().optional(),
  task: z.string().optional(),
  target: z.string().optional(),
  subtype: z.string().optional(),
});

export const AssignmentSchema = z.object({
  zoneId: z.string(),
  priority: z.number().int().positive(),
  actions: z.array(ActionSchema),
});

export const PlanSchema = z.object({
  version: z.string(),
  assignments: z.array(AssignmentSchema),
  notes: z.string(),
  coverage: z.object({
    total_zones: z.number(),
    covered_zones: z.number(),
    coverage_percentage: z.number(),
    resources_deployed: z.object({
      pumps: z.number(),
      sandbags: z.number(),
      crews: z.number(),
    }),
  }).optional(),
});

// Alerts and communications
export const AlertSchema = z.object({
  id: z.string(),
  zoneId: z.string(),
  severity: AlertSeveritySchema,
  type: AlertTypeSchema,
  crewId: z.string().optional(),
  title: z.string(),
  description: z.string(),
  eta: z.string().nullable(),
  status: AlertStatusSchema,
  timestamp: z.string(),
});

export const CommunicationSchema = z.object({
  id: z.string(),
  channel: z.string(),
  from: z.string(),
  text: z.string(),
  timestamp: z.string(),
});

// Gauges and monitoring
export const GaugeSchema = z.object({
  id: z.string(),
  name: z.string(),
  lat: z.number(),
  lng: z.number(),
  level_m: z.number(),
  trend: TrendSchema,
  alert_threshold: z.number(),
  critical_threshold: z.number(),
  last_updated: z.string(),
});

// UI state
export const MapLayerSchema = z.object({
  id: z.string(),
  name: z.string(),
  visible: z.boolean(),
  opacity: z.number().min(0).max(1),
});

export const TimeHorizonSchema = z.enum(["6h", "12h", "24h", "48h", "72h"]);

export type RiskBand = z.infer<typeof RiskBandSchema>;
export type Role = z.infer<typeof RoleSchema>;
export type CrewStatus = z.infer<typeof CrewStatusSchema>;
export type EquipmentStatus = z.infer<typeof EquipmentStatusSchema>;
export type AlertSeverity = z.infer<typeof AlertSeveritySchema>;
export type AlertType = z.infer<typeof AlertTypeSchema>;
export type AlertStatus = z.infer<typeof AlertStatusSchema>;
export type Trend = z.infer<typeof TrendSchema>;

export type RiskDriver = z.infer<typeof RiskDriverSchema>;
export type RiskPoint = z.infer<typeof RiskPointSchema>;
export type DamageIndex = z.infer<typeof DamageIndexSchema>;
export type ZoneProperties = z.infer<typeof ZonePropertiesSchema>;
export type GeoJSONFeature = z.infer<typeof GeoJSONFeatureSchema>;
export type GeoJSON = z.infer<typeof GeoJSONSchema>;

export type Depot = z.infer<typeof DepotSchema>;
export type Equipment = z.infer<typeof EquipmentSchema>;
export type Crew = z.infer<typeof CrewSchema>;
export type Resources = z.infer<typeof ResourcesSchema>;

export type Action = z.infer<typeof ActionSchema>;
export type Assignment = z.infer<typeof AssignmentSchema>;
export type Plan = z.infer<typeof PlanSchema>;

export type Alert = z.infer<typeof AlertSchema>;
export type Communication = z.infer<typeof CommunicationSchema>;

export type Gauge = z.infer<typeof GaugeSchema>;

export type MapLayer = z.infer<typeof MapLayerSchema>;
export type TimeHorizon = z.infer<typeof TimeHorizonSchema>;

export type UserStatus = 'active' | 'inactive' | 'suspended';

export interface SystemUser {
  id: string;
  username: string;
  password: string;
  email: string;
  firstName: string;
  lastName: string;
  role: Role;
  department: string;
  phone?: string;
  location?: string;
  status: UserStatus;
  lastLogin: string | null;
  zones: string[];
  permissions: string[];
  createdAt: string;
  updatedAt?: string;
}

// Application context types
export interface AppContextType {
  currentRole: Role | null;
  setCurrentRole: (role: Role | null) => void;
  selectedZone: string | null;
  setSelectedZone: (zoneId: string | null) => void;
  timeHorizon: TimeHorizon;
  setTimeHorizon: (horizon: TimeHorizon) => void;
  darkMode: boolean;
  setDarkMode: (enabled: boolean) => void;
}

export interface ViewState {
  center: [number, number];
  zoom: number;
  layers: MapLayer[];
}

export interface ZoneDetailsState {
  zone: ZoneProperties | null;
  risk: RiskPoint | null;
  damage: DamageIndex | null;
  assignments: Assignment[];
  alerts: Alert[];
}

// Pipeline outputs
export interface PipelineScenarioSummary {
  scenario: string;
  generated_at?: string;
  timestamps?: number;
  total_rows?: number;
  mode?: string;
  total_units?: number;
  file?: string;
}

// Live simulation for St. Louis corridor
export interface StageProbability {
  stage: string;
  level_ft: number;
  probability: number;
}

export interface StationSimulationState {
  code: string;
  name: string;
  role: 'target' | 'sensor';
  current_level_ft: number;
  current_level_m: number;
  predicted_level_ft: number;
  predicted_level_m: number;
  probability_exceedance: number;
  trend_ft_per_hr: number;
  last_updated: string;
}

export interface FloodSimulationState {
  ticked_at: string;
  interval_seconds: number;
  horizon_hours: number;
  target_station: StationSimulationState;
  sensor_stations: StationSimulationState[];
  critical_stages: StageProbability[];
}

// River level prediction (backend model output)
export interface RiverLevelPrediction {
  gauge_id: string;
  gauge_name: string;
  river_name?: string;
  prediction_time: string;
  predicted_level: number;
  confidence_level: number;
  risk_level: 'low' | 'moderate' | 'high' | 'severe';
  trend_per_hour: number;
  data_points_used: number;
}

export interface PipelineScenarioInfo {
  name: string;
  source_file?: string;
  total_units?: number | null;
  max_units_per_zone?: number | null;
  last_run_at?: string | null;
  latest_summary?: PipelineScenarioSummary | null;
  latest_allocation_file?: string | null;
  result_path?: string | null;
}

export interface PipelineAllocationRow {
  timestamp: string;
  scenario: string;
  zone_id: string;
  zone_name: string;
  impact_level: string;
  allocation_mode: string;
  river_level_pred: number | null;
  global_pf: number | null;
  pf_zone: number | null;
  vulnerability: number | null;
  is_critical_infra: boolean;
  units_allocated: number;
}

export interface PipelineZoneAllocationSummary {
  zone_id: string;
  zone_name: string;
  is_critical_infra: boolean;
  total_units: number;
  entries: number;
  latest_timestamp: string;
  latest_units: number;
  last_impact?: string;
}

export interface PipelineAllocationsSummaryTotals {
  total_units: number;
  critical_units: number;
  zone_count: number;
}

export interface PipelineAllocationsSummary {
  totals: PipelineAllocationsSummaryTotals;
  zones: PipelineZoneAllocationSummary[];
}

export interface PipelineAllocationsMetaFilters {
  latest: boolean;
  timestamp: string | null;
  zone: string | null;
  impact: string | null;
  criticalOnly: boolean;
  limit: number | null;
}

export interface PipelineAllocationsMeta {
  scenario: string;
  file: string;
  total_rows: number;
  returned_rows: number;
  filters: PipelineAllocationsMetaFilters;
  time_range: {
    start: string | null;
    end: string | null;
  };
}

export interface PipelineAllocationsResponse {
  meta: PipelineAllocationsMeta;
  summary: PipelineAllocationsSummary;
  data: PipelineAllocationRow[];
}

export interface PipelineStageStatus {
  stage: string;
  attempt: number;
  returncode: number;
  stdout: string;
  stderr: string;
}

export interface PipelineScenarioStatus {
  scenario: string;
  completed: boolean;
  stages: PipelineStageStatus[];
}

export type PipelineStatusMap = Record<string, PipelineScenarioStatus>;
