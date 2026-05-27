export type PaymentMethod = 'cash' | 'card' | 'mobile_money' | 'telebirr';

export interface PaymentRequest {
  receiptId: number;
  method: PaymentMethod;
  amount: number;
}

export interface PaymentResult {
  id: number;
  receiptId: number;
  method: PaymentMethod;
  amount: number;
  status: 'paid' | 'failed' | 'cancelled';
  processedAt: string;
  reference: string | null;
}
