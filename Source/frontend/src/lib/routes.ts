export const ADMIN_BASE_PATH = '/administrator';

export const ADMIN_PATH_ALIASES = [ADMIN_BASE_PATH, '/admin'] as const;

export const getAdminPath = (segment: string) => {
  const normalized = segment.replace(/^\/+/, '');
  return `${ADMIN_BASE_PATH}/${normalized}`;
};
