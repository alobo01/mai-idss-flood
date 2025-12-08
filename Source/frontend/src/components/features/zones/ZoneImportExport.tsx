import type { GeoJSON } from '@/types';

export const handleExport = (zones: GeoJSON) => {
  const dataStr = JSON.stringify(zones, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `zones-${new Date().toISOString().split('T')[0]}.geojson`;
  link.click();

  URL.revokeObjectURL(url);
};

export const validateImportedData = (importedData: any, validateGeoJSONFeature: Function, validateZoneProperties: Function) => {
  if (importedData.type !== "FeatureCollection") {
    throw new Error('Invalid GeoJSON: must be a FeatureCollection');
  }

  if (!importedData.features || !Array.isArray(importedData.features)) {
    throw new Error('Invalid GeoJSON: features array is required');
  }

  // Validate all features
  const errors: string[] = [];
  const zoneIds: string[] = [];

  importedData.features.forEach((feature: any, index: number) => {
    const featureErrors = validateGeoJSONFeature(feature);
    featureErrors.forEach((error: string) => {
      errors.push(`Feature ${index + 1}: ${error}`);
    });

    if (feature.properties && feature.properties.id) {
      if (zoneIds.includes(feature.properties.id)) {
        errors.push(`Feature ${index + 1}: Duplicate zone ID '${feature.properties.id}'`);
      }
      zoneIds.push(feature.properties.id);
    }

    if (feature.properties) {
      const propErrors = validateZoneProperties(feature.properties);
      propErrors.forEach((error: string) => {
        errors.push(`Feature ${index + 1}: ${error}`);
      });
    }
  });

  if (errors.length > 0) {
    throw new Error(errors.join('\n'));
  }

  return importedData;
};