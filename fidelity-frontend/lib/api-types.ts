export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type Role =
  | 'ADMIN'
  | 'GLOBAL_ADMIN'
  | 'CUSTOMER_ADMIN'
  | 'FRANCHISE_MANAGER'
  | 'STORE_MANAGER'
  | 'CASHIER'
  | 'USER';

export interface WalletBalance {
  scope: 'GLOBAL' | 'CUSTOMER' | 'FRANCHISE' | 'STORE';
  scope_id: string | null;
  points: number;
  as_brl: number | null;
}

export interface WalletCoupon {
  offer_id: string;
  available_count: number;
  redeemed_count: number;
}

export interface WalletResponse {
  balances: WalletBalance[];
  coupons: WalletCoupon[];
}

export interface CouponType {
  id: string;
  redeem_type: 'BRL' | 'PERCENTAGE' | 'FREE_SKU';
  discount_amount_brl: number | null;
  discount_amount_percentage: number | null;
  sku_specific: boolean;
  valid_skus: string[] | null;
}

export interface OfferAsset {
  id: string;
  kind: 'BANNER' | 'THUMB' | 'DETAIL';
  url: string;
}

export interface CouponOffer {
  id: string;
  entity_scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE';
  entity_id: string;
  initial_quantity: number;
  current_quantity: number;
  max_per_customer: number;
  points_cost: number;
  is_active: boolean;
  start_at: string | null;
  end_at: string | null;
  coupon_type: CouponType;
  assets: OfferAsset[];
  created_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface BuyCouponResponse {
  coupon_id: string;
  code: string;
  qr: {
    format: string;
    data: string;
  };
}

export interface CreateCouponTypeRequest {
  redeem_type: CouponType['redeem_type'];
  discount_amount_brl?: number | null;
  discount_amount_percentage?: number | null;
  sku_specific?: boolean;
  valid_skus?: string[] | null;
}

export interface CouponOfferCreateRequest {
  entity_scope: CouponOffer['entity_scope'];
  entity_id: string;
  coupon_type_id: string;
  initial_quantity: number;
  max_per_customer: number;
  points_cost: number;
  start_at?: string | null;
  end_at?: string | null;
  is_active?: boolean;
  customer_segment?: Record<string, unknown> | null;
}

export interface CouponOfferDetail extends CouponOffer {
  created_at: string;
  customer_segment?: Record<string, unknown> | null;
}

export interface AdminCouponType {
  id: string;
  sku_specific: boolean;
  redeem_type: CouponType['redeem_type'];
  discount_amount_brl: number | null;
  discount_amount_percentage: number | null;
  valid_skus: string[] | null;
}

export interface AdminCouponOffer {
  id: string;
  entity_scope: CouponOffer['entity_scope'];
  entity_id: string;
  coupon_type_id: string;
  customer_segment: Record<string, unknown> | null;
  initial_quantity: number;
  current_quantity: number;
  max_per_customer: number;
  points_cost: number;
  is_active: boolean;
  start_at: string | null;
  end_at: string | null;
  created_at: string;
}

export interface CouponOfferStats {
  total_issued: number;
  total_reserved: number;
  total_redeemed: number;
  total_cancelled: number;
  total_expired: number;
  redemption_by_store: { store_id: string; store_name: string; count: number }[];
  redemption_timeline: { date: string | null; count: number }[];
}

export interface Customer {
  id: string;
  cnpj: string;
  name: string;
  contact_email?: string;
  phone?: string;
  created_at: string;
}

export interface Franchise {
  id: string;
  customer_id: string;
  cnpj?: string;
  name: string;
  created_at: string;
}

export interface Store {
  id: string;
  franchise_id: string;
  cnpj?: string;
  name: string;
  location?: Record<string, unknown>;
  created_at: string;
}

export interface PointTransaction {
  id: number;
  person_id: string;
  scope: 'GLOBAL' | 'CUSTOMER' | 'FRANCHISE' | 'STORE';
  scope_id: string | null;
  store_id: string | null;
  order_id: string | null;
  delta: number;
  details: Record<string, unknown>;
  created_at: string;
  expires_at: string | null;
}

export interface MyCouponWithCode {
  id: string;
  offer_id: string;
  status: 'ISSUED' | 'RESERVED' | 'REDEEMED' | 'CANCELLED' | 'EXPIRED';
  issued_at: string;
  code: string;
  qr: {
    format: string;
    data: string;
  };
  offer: {
    entity_scope: 'CUSTOMER' | 'FRANCHISE' | 'STORE';
    entity_id: string;
    points_cost: number;
    is_active: boolean;
  };
  coupon_type: {
    redeem_type: 'BRL' | 'PERCENTAGE' | 'FREE_SKU';
    discount_amount_brl: number | null;
    discount_amount_percentage: number | null;
  };
}

