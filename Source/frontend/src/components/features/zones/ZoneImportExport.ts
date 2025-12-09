import type { GeoJSON as GeoJSONType } from '@/types';

export const downloadZonesAsJson = (zones: GeoJSONType) => {
  const dataStr = JSON.stringify(zones, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);

  const link = document.createElement('a');
  link.href = url;
  link.download = `zones-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const parseUploadedFile = (file: File): Promise<GeoJSONType> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsed = JSON.parse(content);
        resolve(parsed);
      } catch (error) {
        reject(new Error('Invalid JSON file'));
      }
    };

    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
};

export const validateUploadedFile = (content: any): string[] => {
  const errors: string[] = [];

  if (!content || typeof content !== 'object') {
    errors.push('File must contain a valid JSON object');
    return errors;
  }

  if (!content.type) {
    errors.push('GeoJSON must have a type property');
  }

  if (!content.features || !Array.isArray(content.features)) {
    errors.push('GeoJSON must have a features array');
  } else {
    content.features.forEach((feature: any, index: number) => {
      if (!feature.type || feature.type !== 'Feature') {
        errors.push(`Feature ${index + 1}: Must be a valid GeoJSON Feature`);
      }

      if (!feature.geometry) {
        errors.push(`Feature ${index + 1}: Must have geometry`);
      }

      if (!feature.properties) {
        errors.push(`Feature ${index + 1}: Must have properties`);
      }
    });
  }

  return errors;
};

// Alias for backward compatibility
export const handleExport = downloadZonesAsJson;
export const validateImportedData = validateUploadedFile;