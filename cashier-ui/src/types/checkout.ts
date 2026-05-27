// ---------------------------------------------------------------------------
// Checkout types — aligned with Django backend models and serializers
// ---------------------------------------------------------------------------

export type CheckoutSessionStatus =
  | 'OPEN'
  | 'CONFIRMED'
  | 'PAYMENT_PENDING'
  | 'COMPLETED'
  | 'CANCELLED';

export type ItemSource = 'MANUAL' | 'VISION' | 'BARCODE' | 'WEIGHTED';

export type ItemReviewStatus =
  | 'NOT_REQUIRED'
  | 'NEEDS_REVIEW'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'REPLACED';

export type ItemStatus = 'ACTIVE' | 'NEEDS_REVIEW' | 'REMOVED';

export interface CheckoutItem {
  id: number;
  checkout_session: number;
  product: number;
  product_name: string;
  product_sku: string;
  unit_type: string;
  quantity: string; // decimal string from backend
  unit_price: string;
  subtotal: string;
  confidence: string | null;
  source: ItemSource;
  status: ItemStatus;
  review_status: ItemReviewStatus;
  note: string;
  created_at: string;
  updated_at: string;
}

export interface CheckoutSession {
  id: number;
  cashier: number | null;
  cashier_username: string | null;
  status: CheckoutSessionStatus;
  subtotal: string;
  total_amount: string;
  receipt_id: number | null;
  receipt_payment_status: string | null;
  note: string;
  items: CheckoutItem[];
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  cancelled_at: string | null;
}
