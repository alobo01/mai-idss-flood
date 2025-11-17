/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_MAP_TILES_URL: string
  readonly VITE_DEFAULT_ADMIN_USERNAME?: string
  readonly VITE_DEFAULT_ADMIN_PASSWORD?: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
