import { apiClient } from './client';

export type PaymentMethod = 'CASH' | 'CARD' | 'MOBILE_MONEY' | 'TELEBIRR' | 'DEMO';
export type PaymentStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface Payment {
  id: number;
  receipt: number;
  checkout_session: number;
  amount: string;
  method: PaymentMethod;
  status: PaymentStatus;
  transaction_reference: string | null;
  provider_name: string | null;
  created_at: string;
}

export interface SimulatePaymentRequest {
  receipt_id: number;
  method?: PaymentMethod;
  status?: PaymentStatus;
  amount?: string;
}

/**
 * POST /api/payments/simulate/
 * Simulates a payment for a receipt.
 */
export async function simulatePayment(req: SimulatePaymentRequest): Promise<Payment> {
  const res = await apiClient.post<Payment>('/api/payments/simulate/', req);
  return res.data;
}
