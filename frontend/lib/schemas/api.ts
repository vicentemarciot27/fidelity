import { z } from "zod"

export const apiResponseSchema = z.object({
  success: z.boolean(),
  data: z.any().optional(),
  message: z.string().optional(),
  errors: z.record(z.array(z.string())).optional(),
})

export const paginationSchema = z.object({
  page: z.number(),
  limit: z.number(),
  total: z.number(),
  totalPages: z.number(),
})

export const paginatedResponseSchema = z.object({
  data: z.array(z.any()),
  pagination: paginationSchema,
})

export const apiErrorSchema = z.object({
  message: z.string(),
  code: z.string().optional(),
  status: z.number().optional(),
})

export type ApiResponse<T = any> = z.infer<typeof apiResponseSchema> & { data?: T }
export type PaginatedResponse<T> = Omit<z.infer<typeof paginatedResponseSchema>, "data"> & { data: T[] }
export type ApiError = z.infer<typeof apiErrorSchema>
