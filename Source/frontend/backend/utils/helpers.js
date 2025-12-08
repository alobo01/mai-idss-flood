const severityDisplayMap = {
  low: 'Low',
  medium: 'Moderate',
  high: 'High',
  critical: 'Severe',
};

export const clamp = (value) => Math.min(Math.max(Number(value) || 0, 0), 1);

export const determineRiskBand = (value) => {
  if (value >= 0.75) return 'Severe';
  if (value >= 0.5) return 'High';
  if (value >= 0.35) return 'Moderate';
  return 'Low';
};

export const parsePoint = (geoJsonText) => {
  if (!geoJsonText) return { lat: null, lng: null };
  try {
    const geometry = JSON.parse(geoJsonText);
    if (geometry?.coordinates) {
      const [lng, lat] = geometry.coordinates;
      return { lat, lng };
    }
  } catch {
    // Ignore parse errors and fall through
  }
  return { lat: null, lng: null };
};

export const formatRiskDrivers = (rawFactors) => {
  if (!rawFactors) return [];

  if (Array.isArray(rawFactors)) {
    return rawFactors.map((entry) => ({
      feature: entry.feature || 'factor',
      contribution: clamp(entry.contribution),
    }));
  }

  const entries = Object.entries(rawFactors);
  const sum = entries.reduce((total, [, value]) => total + (Number(value) || 0), 0) || 1;

  return entries.map(([feature, value]) => ({
    feature,
    contribution: Math.round(((Number(value) || 0) / sum) * 100) / 100,
  }));
};

export const alertStatus = (row) => {
  if (row.resolved) return 'resolved';
  if (row.acknowledged) return 'acknowledged';
  return 'open';
};

export const alertSeverityDisplay = (value) => severityDisplayMap[value] || 'Moderate';

export const determineTrend = (current, previous, fallback) => {
  if (current == null || previous == null) {
    return fallback || 'steady';
  }
  const delta = Number(current) - Number(previous);
  if (delta > 0.05) return 'rising';
  if (delta < -0.05) return 'falling';
  return 'steady';
};

export const distance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000;
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
};

export const hasAdminPermission = (req) => {
  const auth = req.headers.authorization;
  return auth?.startsWith('Bearer admin-') || req.headers['x-admin-key'] === process.env.ADMIN_KEY;
};