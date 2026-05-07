import type { DetectedProduct } from './product';

export type CheckoutSessionStatus = 'open' | 'completed' | 'cancelled';

export interface CheckoutSession {
  id: number;
  sessionCode: string;
  cashierId: number;
  cashierName: string;
  status: CheckoutSessionStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CheckoutItem {
  id: number;
  sessionId: number;
  product: DetectedProduct['product'];
  quantity: number | null;
  weight: number | null;
  unitPrice: number;
  subtotal: number;
  source: DetectedProduct['source'];
}

export interface CheckoutSummary {
  session: CheckoutSession;
  items: CheckoutItem[];
  subtotal: number;
  total: number;
}
