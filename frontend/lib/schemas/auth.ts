import { z } from "zod"

export const loginSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(6, "Senha deve ter pelo menos 6 caracteres"),
})

export const registerSchema = z
  .object({
    name: z.string().min(2, "Nome deve ter pelo menos 2 caracteres"),
    email: z.string().email("Email inválido"),
    password: z.string().min(6, "Senha deve ter pelo menos 6 caracteres"),
    confirmPassword: z.string(),
    phone: z.string().optional(),
    cpf: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Senhas não coincidem",
    path: ["confirmPassword"],
  })

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  phone: z.string().optional(),
  cpf: z.string().optional(),
  role: z.enum(["customer", "store_manager", "franchise_admin", "super_admin"]),
  customerId: z.string().optional(),
  franchiseId: z.string().optional(),
  storeId: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const authTokensSchema = z.object({
  accessToken: z.string(),
  refreshToken: z.string(),
  expiresIn: z.number(),
})

export const authResponseSchema = z.object({
  user: userSchema,
  tokens: authTokensSchema,
})

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type User = z.infer<typeof userSchema>
export type AuthTokens = z.infer<typeof authTokensSchema>
export type AuthResponse = z.infer<typeof authResponseSchema>
