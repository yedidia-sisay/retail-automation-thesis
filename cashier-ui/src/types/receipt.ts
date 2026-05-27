// Aligned with backend ReceiptSerializer and ReceiptLineSerializer

export interface ReceiptLine {
  id: number;
  product: number;
  product_name: string;
  product_sku: string;
  quantity: string;
  unit_price: string;
  subtotal: string;
  source: 'VISION' | 'BARCODE' | 'MANUAL' | 'WEIGHTED';
  created_at: string;
}

export interface Receipt {
  id: number;
  receipt_number: string;
  checkout_session: number;
  cashier: number | null;
  total: string;
  payment_status: 'PENDING' | 'PAID' | 'FAILED' | 'CANCELLED';
  erp_status: string;
  erp_reference: string | null;
  erp_synced_at: string | null;
  created_at: string;
  lines: ReceiptLine[];
}
