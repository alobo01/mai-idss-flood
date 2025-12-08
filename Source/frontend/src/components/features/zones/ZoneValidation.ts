import type { ZoneProperties, GeoJSONFeature } from '@/types';

export const validateZoneId = (id: string, existingIds: string[]): string[] => {
  const errors: string[] = [];

  if (!id || id.trim() === '') {
    errors.push('Zone ID is required');
  }

  if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(id)) {
    errors.push('Zone ID must start with a letter and contain only letters, numbers, underscores, and hyphens');
  }

  if (existingIds.includes(id)) {
    errors.push('Zone ID must be unique');
  }

  return errors;
};

export const validateZoneProperties = (properties: ZoneProperties): string[] => {
  const errors: string[] = [];

  if (!properties.name || properties.name.trim() === '') {
    errors.push('Zone name is required');
  }

  if (properties.population < 0) {
    errors.push('Population must be a non-negative number');
  }

  if (properties.admin_level < 1 || properties.admin_level > 15) {
    errors.push('Admin level must be between 1 and 15');
  }

  if (properties.critical_assets.some(asset => !asset || asset.trim() === '')) {
    errors.push('Critical asset names cannot be empty');
  }

  return errors;
};

export const validateGeoJSONFeature = (feature: any): string[] => {
  const errors: string[] = [];

  if (feature.type !== 'Feature') {
    errors.push('Invalid GeoJSON feature type');
  }

  if (!feature.properties) {
    errors.push('Feature properties are required');
  }

  if (!feature.geometry) {
    errors.push('Feature geometry is required');
  }

  if (feature.geometry.type !== 'Polygon') {
    errors.push('Only Polygon geometry is supported');
  }

  if (!feature.geometry.coordinates || !Array.isArray(feature.geometry.coordinates)) {
    errors.push('Invalid polygon coordinates');
  }

  return errors;
};

export const validateAllZones = (zones: any): string[] => {
  const errors: string[] = [];

  if (!zones.type) {
    errors.push('GeoJSON type is required');
  }

  if (!zones.features || !Array.isArray(zones.features)) {
    errors.push('GeoJSON features array is required');
  } else {
    zones.features.forEach((feature: GeoJSONFeature, index: number) => {
      const featureErrors = validateGeoJSONFeature(feature);
      featureErrors.forEach(error => {
        errors.push(`Feature ${index + 1}: ${error}`);
      });
    });
  }

  return errors;
};