export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'cancelled';
export type ERPSyncStatus = 'not_synced' | 'synced' | 'failed' | 'retrying';

export interface ReceiptLine {
  id: number;
  productName: string;
  quantity: number | null;
  weight: number | null;
  unitPrice: number;
  subtotal: number;
  source: 'vision' | 'barcode' | 'manual' | 'weighted';
}

export interface Receipt {
  id: number;
  receiptNumber: string;
  sessionId: number;
  cashierName: string;
  storeName: string;
  createdAt: string;
  lines: ReceiptLine[];
  subtotal: number;
  tax: number;
  total: number;
  paymentStatus: PaymentStatus;
  erpSyncStatus: ERPSyncStatus;
  erpReference: string | null;
}
