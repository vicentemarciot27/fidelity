import { apiClient } from "./client"
import { z } from "zod"

const createUserSchema = z.object({
  name: z.string(),
  email: z.string().email(),
  password: z.string(),
  role: z.enum(["store_manager", "franchise_admin", "super_admin"]),
  franchiseId: z.string().optional(),
  storeId: z.string().optional(),
  phone: z.string().optional(),
})

export type CreateUserInput = z.infer<typeof createUserSchema>

export const adminApi = {
  // Create user with specific role (admin only)
  createUser: async (data: CreateUserInput) => {
    const response = await apiClient.post("/admin/users", data)
    return response.data
  },

  // List users with filtering by role
  getUsers: async (filters?: { role?: string; franchiseId?: string }) => {
    const params = new URLSearchParams()
    if (filters?.role) params.append("role", filters.role)
    if (filters?.franchiseId) params.append("franchiseId", filters.franchiseId)

    const response = await apiClient.get(`/admin/users?${params}`)
    return response.data
  },

  // Update user role and permissions
  updateUserRole: async (userId: string, role: string, franchiseId?: string, storeId?: string) => {
    const response = await apiClient.patch(`/admin/users/${userId}/role`, {
      role,
      franchiseId,
      storeId,
    })
    return response.data
  },
}
