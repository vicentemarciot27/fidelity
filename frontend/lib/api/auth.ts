import { apiClient } from "./client"
import { authResponseSchema, type LoginInput, type RegisterInput, type AuthResponse } from "@/lib/schemas/auth"

export const authApi = {
  async login(credentials: LoginInput): Promise<AuthResponse> {
    const response = await apiClient.post<any>("/auth/login", credentials)

    if (response.success && response.data) {
      try {
        // Adapta o formato da resposta da API para o formato esperado pelo frontend
        const adaptedData = {
          user: response.data.user || {
            id: "user_id",
            email: credentials.email,
            name: "Usuário",
            role: "customer",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          tokens: {
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresIn: 3600 // valor padrão caso não exista
          }
        }
        
        const validatedData = authResponseSchema.parse(adaptedData)
        apiClient.setAccessToken(validatedData.tokens.accessToken)
        return validatedData
      } catch (error) {
        console.error("Erro na validação dos dados de autenticação:", error)
        throw new Error("Formato de resposta inválido")
      }
    }

    throw new Error(response.message || "Erro no login")
  },

  async register(data: RegisterInput): Promise<AuthResponse> {
    const response = await apiClient.post<any>("/auth/register", data)

    if (response.success && response.data) {
      try {
        // Adapta o formato da resposta da API para o formato esperado pelo frontend
        const adaptedData = {
          user: response.data.user || {
            id: "user_id",
            email: data.email,
            name: data.name,
            role: "customer",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          tokens: {
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresIn: 3600 // valor padrão caso não exista
          }
        }
        
        const validatedData = authResponseSchema.parse(adaptedData)
        apiClient.setAccessToken(validatedData.tokens.accessToken)
        return validatedData
      } catch (error) {
        console.error("Erro na validação dos dados de cadastro:", error)
        throw new Error("Formato de resposta inválido")
      }
    }

    throw new Error(response.message || "Erro no cadastro")
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post("/auth/logout")
    } finally {
      apiClient.setAccessToken(null)
    }
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await apiClient.post<any>("/auth/refresh")

    if (response.success && response.data) {
      try {
        // Adapta o formato da resposta da API para o formato esperado pelo frontend
        const adaptedData = {
          user: response.data.user || {
            id: "user_id", 
            email: "user@example.com",
            name: "Usuário",
            role: "customer",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          },
          tokens: {
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresIn: 3600 // valor padrão caso não exista
          }
        }
        
        const validatedData = authResponseSchema.parse(adaptedData)
        apiClient.setAccessToken(validatedData.tokens.accessToken)
        return validatedData
      } catch (error) {
        console.error("Erro na validação dos dados de renovação do token:", error)
        throw new Error("Formato de resposta inválido")
      }
    }

    throw new Error(response.message || "Erro ao renovar token")
  },

  async getCurrentUser(): Promise<AuthResponse["user"]> {
    const response = await apiClient.get<AuthResponse["user"]>("/auth/me")

    if (response.success && response.data) {
      return response.data
    }

    throw new Error(response.message || "Erro ao buscar usuário")
  },
}
