import { apiClient } from './client';
import type { CheckoutSession, CheckoutItem } from '../types/checkout';

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

export async function createSession(note = ''): Promise<CheckoutSession> {
  const res = await apiClient.post<CheckoutSession>('/api/checkout/sessions/', { note });
  return res.data;
}

export async function getSession(sessionId: number): Promise<CheckoutSession> {
  const res = await apiClient.get<CheckoutSession>(`/api/checkout/sessions/${sessionId}/`);
  return res.data;
}

export async function cancelSession(sessionId: number): Promise<CheckoutSession> {
  const res = await apiClient.post<CheckoutSession>(
    `/api/checkout/sessions/${sessionId}/cancel/`,
  );
  return res.data;
}

export async function confirmSession(sessionId: number): Promise<unknown> {
  const res = await apiClient.post(`/api/checkout/sessions/${sessionId}/confirm/`);
  return res.data;
}

// ---------------------------------------------------------------------------
// Items — actions on individual checkout items
// ---------------------------------------------------------------------------

export async function acceptItem(itemId: number, note = ''): Promise<CheckoutItem> {
  const res = await apiClient.post<CheckoutItem>(`/api/checkout/items/${itemId}/accept/`, {
    note,
  });
  return res.data;
}

export async function rejectItem(itemId: number, note = ''): Promise<CheckoutItem> {
  const res = await apiClient.post<CheckoutItem>(`/api/checkout/items/${itemId}/reject/`, {
    note,
  });
  return res.data;
}

export async function removeItem(itemId: number): Promise<CheckoutItem> {
  const res = await apiClient.post<CheckoutItem>(`/api/checkout/items/${itemId}/remove/`);
  return res.data;
}

export async function changeItemQuantity(
  itemId: number,
  quantity: string,
  note = '',
): Promise<CheckoutItem> {
  const res = await apiClient.patch<CheckoutItem>(
    `/api/checkout/items/${itemId}/change-quantity/`,
    { quantity, note },
  );
  return res.data;
}

export async function replaceItemProduct(
  itemId: number,
  productId: number,
  quantity?: string,
  note = '',
): Promise<CheckoutItem> {
  const res = await apiClient.post<CheckoutItem>(
    `/api/checkout/items/${itemId}/replace-product/`,
    { product_id: productId, quantity, note },
  );
  return res.data;
}

// ---------------------------------------------------------------------------
// Add items to a session
// ---------------------------------------------------------------------------

export async function addManualItem(
  sessionId: number,
  productId: number,
  quantity: string,
): Promise<CheckoutItem> {
  const res = await apiClient.post<CheckoutItem>(
    `/api/checkout/sessions/${sessionId}/add-manual-item/`,
    { product_id: productId, quantity },
  );
  return res.data;
}

export async function addBarcodeItem(
  sessionId: number,
  barcode: string,
  quantity = '1.000',
): Promise<CheckoutSession> {
  const res = await apiClient.post<CheckoutSession>(
    `/api/checkout/sessions/${sessionId}/add-barcode/`,
    { barcode, quantity },
  );
  return res.data;
}

// ---------------------------------------------------------------------------
// Weighted item
// ---------------------------------------------------------------------------

export interface WeightedItemEntry {
  id: number;
  checkout_session: number;
  checkout_item: number | null;
  product: number;
  product_name: string;
  weight: string;
  weight_unit: 'KG' | 'GRAM';
  unit_price: string;
  subtotal: string;
  weight_source: 'MANUAL' | 'OCR';
  raw_ocr_text: string | null;
  created_at: string;
}

export async function addWeightedItem(
  sessionId: number,
  productId: number,
  weight: string,
  weightUnit: 'KG' | 'GRAM' = 'KG',
  weightSource: 'MANUAL' | 'OCR' = 'MANUAL',
): Promise<WeightedItemEntry> {
  const res = await apiClient.post<WeightedItemEntry>(
    `/api/checkout/sessions/${sessionId}/add-weighted-item/`,
    {
      product_id: productId,
      weight,
      weight_unit: weightUnit,
      weight_source: weightSource,
    },
  );
  return res.data;
}
