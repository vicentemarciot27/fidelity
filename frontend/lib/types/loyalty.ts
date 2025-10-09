export interface Customer {
  id: string
  name: string
  email: string
  phone?: string
  cpf?: string
  points: number
  level: string
  createdAt: string
  updatedAt: string
}

export interface Franchise {
  id: string
  name: string
  cnpj: string
  email: string
  phone: string
  address: string
  createdAt: string
  updatedAt: string
}

export interface Store {
  id: string
  franchiseId: string
  name: string
  address: string
  phone: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface Offer {
  id: string
  title: string
  description: string
  imageUrl?: string
  pointsCost: number
  category: string
  isActive: boolean
  validUntil?: string
  createdAt: string
  updatedAt: string
}

export interface Coupon {
  id: string
  code: string
  customerId: string
  offerId: string
  status: "active" | "used" | "expired"
  expiresAt: string
  usedAt?: string
  storeId?: string
  createdAt: string
  updatedAt: string
}
