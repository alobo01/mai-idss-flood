const rawBaseUrl = () => {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (!raw || raw.trim().length === 0) {
    return '/api';
  }
  return raw.trim();
};

export const getApiBaseUrl = (): string => {
  const base = rawBaseUrl().replace(/\/+$/, '');
  if (base.length === 0) {
    return '/api';
  }
  // If the base is a full URL (http:// or https://), don't add /api to it
  // since the backend already has /api in the endpoints
  if (base.startsWith('http://') || base.startsWith('https://')) {
    return base;
  }
  // For relative paths like '/api', use them as-is
  return base.toLowerCase().endsWith('/api') ? base : `${base}/api`;
};

export const buildApiUrl = (endpoint: string): string => {
  const base = getApiBaseUrl();
  const normalized = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${normalized}`;
};
