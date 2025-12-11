import { GeoJSON, RiskPoint, Alert, PipelineRuleBasedAllocation } from '../types';

// Mock zones data
export const mockZones: GeoJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'Z1N',
        name: 'North Riverfront Floodplain',
        population: 36000,
        critical_assets: ['Chain of Rocks Water Plant', 'Riverport Rail Yard'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.215, 38.76],
          [-90.17, 38.76],
          [-90.17, 38.70],
          [-90.24, 38.70],
          [-90.215, 38.76]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        id: 'Z1S',
        name: 'South Riverfront Floodplain',
        population: 32000,
        critical_assets: ['Anheuser-Busch Brewery', 'River City Pump Station'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.24, 38.63],
          [-90.17, 38.63],
          [-90.17, 38.56],
          [-90.26, 38.56],
          [-90.24, 38.63]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        id: 'Z2',
        name: 'Central Business & Medical Core',
        population: 48000,
        critical_assets: ['Barnes-Jewish Hospital', 'Downtown Power Substation', 'Civic Emergency Center'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.24, 38.66],
          [-90.18, 38.66],
          [-90.18, 38.63],
          [-90.25, 38.63],
          [-90.24, 38.66]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        id: 'Z3',
        name: 'Inland South Residential Plateau',
        population: 54000,
        critical_assets: ['Southwest EMS Station', 'Carondelet Clinic'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.32, 38.62],
          [-90.22, 38.62],
          [-90.22, 38.58],
          [-90.33, 38.58],
          [-90.32, 38.62]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        id: 'Z4',
        name: 'Inland North Residential Plateau',
        population: 58000,
        critical_assets: ['Northside Trauma Center', 'University Health Clinic'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.33, 38.70],
          [-90.22, 38.70],
          [-90.22, 38.64],
          [-90.34, 38.64],
          [-90.33, 38.70]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        id: 'ZC',
        name: 'Central / Special ZIPs',
        population: 8000,
        critical_assets: ['Civic Center Transit Hub', 'City Hall Complex'],
        admin_level: 10
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [-90.22, 38.68],
          [-90.19, 38.68],
          [-90.19, 38.66],
          [-90.23, 38.66],
          [-90.22, 38.68]
        ]]
      }
    }
  ]
};

// Mock risk data
export const mockRiskData: RiskPoint[] = [
  {
    zoneId: 'Z1N',
    risk: 0.85,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.56 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.38 },
      { feature: 'soil_saturation', contribution: 0.2 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'Severe',
    etaHours: 4
  },
  {
    zoneId: 'Z1S',
    risk: 0.65,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.55 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.38 },
      { feature: 'soil_saturation', contribution: 0.2 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'High',
    etaHours: 6
  },
  {
    zoneId: 'Z2',
    risk: 0.45,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.52 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.35 },
      { feature: 'soil_saturation', contribution: 0.21 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'Moderate',
    etaHours: 8
  },
  {
    zoneId: 'Z3',
    risk: 0.25,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.49 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.33 },
      { feature: 'soil_saturation', contribution: 0.23 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'Low',
    etaHours: 12
  },
  {
    zoneId: 'Z4',
    risk: 0.35,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.51 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.34 },
      { feature: 'soil_saturation', contribution: 0.22 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'Moderate',
    etaHours: 10
  },
  {
    zoneId: 'ZC',
    risk: 0.15,
    drivers: [
      { feature: 'river_gauge_m', contribution: 0.48 },
      { feature: 'forecast_rain_mm_6h', contribution: 0.32 },
      { feature: 'soil_saturation', contribution: 0.23 },
      { feature: 'urban_runoff', contribution: 0.05 }
    ],
    thresholdBand: 'Low',
    etaHours: 16
  }
];

// Mock alerts data
export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    zoneId: 'Z1N',
    title: 'Critical Flood Warning',
    severity: 'Severe',
    message: 'River levels exceeding 35ft, immediate action required',
    timestamp: new Date().toISOString()
  },
  {
    id: 'alert-2',
    zoneId: 'Z1S',
    title: 'Flood Watch',
    severity: 'Moderate',
    message: 'River levels rising, monitor situation closely',
    timestamp: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 'alert-3',
    zoneId: 'Z2',
    title: 'Heavy Rainfall Alert',
    severity: 'Moderate',
    message: 'Forecast predicts 4 inches of rain in next 12 hours',
    timestamp: new Date(Date.now() - 7200000).toISOString()
  }
];

// Mock rule-based pipeline data
export const mockRulePipeline: { allocations: PipelineRuleBasedAllocation[] } = {
  allocations: [
    {
      zone_id: 'Z1N',
      units_allocated: 4,
      impact_level: 'CRITICAL',
      allocation_mode: 'crisp',
      pf: 0.85,
      vulnerability: 0.92
    },
    {
      zone_id: 'Z1S',
      units_allocated: 3,
      impact_level: 'WARNING',
      allocation_mode: 'crisp',
      pf: 0.65,
      vulnerability: 0.73
    },
    {
      zone_id: 'Z2',
      units_allocated: 2,
      impact_level: 'ADVISORY',
      allocation_mode: 'crisp',
      pf: 0.45,
      vulnerability: 0.52
    },
    {
      zone_id: 'Z3',
      units_allocated: 1,
      impact_level: 'NORMAL',
      allocation_mode: 'crisp',
      pf: 0.25,
      vulnerability: 0.31
    },
    {
      zone_id: 'Z4',
      units_allocated: 1,
      impact_level: 'ADVISORY',
      allocation_mode: 'crisp',
      pf: 0.35,
      vulnerability: 0.41
    },
    {
      zone_id: 'ZC',
      units_allocated: 1,
      impact_level: 'NORMAL',
      allocation_mode: 'crisp',
      pf: 0.15,
      vulnerability: 0.18
    }
  ]
};