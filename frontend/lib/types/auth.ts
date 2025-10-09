export interface User {
  id: string
  email: string
  name: string
  phone?: string
  cpf?: string
  role: "customer" | "store_manager" | "franchise_admin" | "super_admin"
  customerId?: string
  franchiseId?: string
  storeId?: string
  createdAt: string
  updatedAt: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  name: string
  email: string
  password: string
  phone?: string
  cpf?: string
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
}
