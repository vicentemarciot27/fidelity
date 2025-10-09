import { z } from "zod"

export const customerSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
  phone: z.string().optional(),
  cpf: z.string().optional(),
  points: z.number(),
  level: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const franchiseSchema = z.object({
  id: z.string(),
  name: z.string(),
  cnpj: z.string(),
  email: z.string().email(),
  phone: z.string(),
  address: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const storeSchema = z.object({
  id: z.string(),
  franchiseId: z.string(),
  name: z.string(),
  address: z.string(),
  phone: z.string(),
  isActive: z.boolean(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const offerSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  imageUrl: z.string().optional(),
  pointsCost: z.number(),
  category: z.string(),
  isActive: z.boolean(),
  validUntil: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export const couponSchema = z.object({
  id: z.string(),
  code: z.string(),
  customerId: z.string(),
  offerId: z.string(),
  status: z.enum(["active", "used", "expired"]),
  expiresAt: z.string(),
  usedAt: z.string().optional(),
  storeId: z.string().optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
})

export type Customer = z.infer<typeof customerSchema>
export type Franchise = z.infer<typeof franchiseSchema>
export type Store = z.infer<typeof storeSchema>
export type Offer = z.infer<typeof offerSchema>
export type Coupon = z.infer<typeof couponSchema>
