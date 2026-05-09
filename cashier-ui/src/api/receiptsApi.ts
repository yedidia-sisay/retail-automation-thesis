import { apiClient } from './client';
import type { Receipt } from '../types/receipt';

export async function getReceipt(receiptId: number): Promise<Receipt> {
  const res = await apiClient.get<Receipt>(`/api/receipts/${receiptId}/`);
  return res.data;
}

export async function getReceiptPrintPreview(receiptId: number): Promise<Receipt & { printable_text: string }> {
  const res = await apiClient.get<Receipt & { printable_text: string }>(
    `/api/receipts/${receiptId}/print-preview/`,
  );
  return res.data;
}
