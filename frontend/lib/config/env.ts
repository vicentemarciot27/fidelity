export const env = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8007",
  APP_ENV: process.env.NODE_ENV || "development",
  JWT_SECRET: process.env.JWT_SECRET || "your-jwt-secret",
} as const

export const isDevelopment = env.APP_ENV === "development"
export const isProduction = env.APP_ENV === "production"
