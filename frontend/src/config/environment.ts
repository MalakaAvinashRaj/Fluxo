export const ENV = {
  NODE_ENV: import.meta.env.NODE_ENV || 'development',
  // Empty string = same-origin (Nginx proxy in production). Falls back to localhost in dev.
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  API_TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_RETRY_ATTEMPTS || '3'),
  RETRY_DELAY: parseInt(import.meta.env.VITE_RETRY_DELAY || '1000'),
  LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || 'info',
} as const

export const isProduction = ENV.NODE_ENV === 'production'
export const isDevelopment = ENV.NODE_ENV === 'development'

export const validateEnvironment = () => {
  // API_BASE_URL is intentionally empty in production (same-origin via Nginx)
  // Nothing strictly required at runtime — keys live server-side
}