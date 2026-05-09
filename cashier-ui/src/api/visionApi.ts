import { apiClient } from './client';
import type { VisionDetectResult } from '../types/product';

/**
 * POST /api/vision/detect/
 * Sends a multipart form with the image file and checkout session ID.
 * Returns detected objects and draft checkout items.
 */
export async function detectProducts(
  sessionId: number,
  imageFile: File,
): Promise<VisionDetectResult> {
  const form = new FormData();
  form.append('checkout_session_id', String(sessionId));
  form.append('image', imageFile);

  const res = await apiClient.post<VisionDetectResult>('/api/vision/detect/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}
