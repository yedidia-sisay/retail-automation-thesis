import { apiClient } from './client';
import type {
  CameraConfig,
  CameraTestResult,
  SKUDetectResult,
  WeightedDetectResult,
} from '../types/camera';

const base = (terminalId: string) => `/api/terminals/${terminalId}`;

// ---------------------------------------------------------------------------
// Camera config
// ---------------------------------------------------------------------------

/** GET /api/terminals/{terminalId}/cameras/ */
export async function getCameraConfigs(terminalId: string): Promise<CameraConfig[]> {
  const res = await apiClient.get<CameraConfig[]>(`${base(terminalId)}/cameras/`);
  return res.data;
}

/** GET /api/terminals/{terminalId}/cameras/{role}/settings/ */
export async function getCameraSettings(
  terminalId: string,
  role: 'sku' | 'weighted',
): Promise<CameraConfig> {
  const res = await apiClient.get<CameraConfig>(
    `${base(terminalId)}/cameras/${role}/settings/`,
  );
  return res.data;
}

/** PATCH /api/terminals/{terminalId}/cameras/{role}/settings/ */
export async function updateCameraSettings(
  terminalId: string,
  role: 'sku' | 'weighted',
  data: Partial<CameraConfig>,
): Promise<CameraConfig> {
  const res = await apiClient.patch<CameraConfig>(
    `${base(terminalId)}/cameras/${role}/settings/`,
    data,
  );
  return res.data;
}

/** POST /api/terminals/{terminalId}/cameras/{role}/test/ */
export async function testCamera(
  terminalId: string,
  role: 'sku' | 'weighted',
): Promise<CameraTestResult> {
  const res = await apiClient.post<CameraTestResult>(
    `${base(terminalId)}/cameras/${role}/test/`,
  );
  return res.data;
}

/**
 * Returns the URL for the camera preview image.
 * Use directly as <img src={previewUrl(...)} />.
 * The browser will send the session cookie automatically.
 */
export function previewUrl(terminalId: string, role: 'sku' | 'weighted'): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${apiBase}/api/terminals/${terminalId}/cameras/${role}/preview/`;
}

// ---------------------------------------------------------------------------
// Detection
// ---------------------------------------------------------------------------

/** POST /api/terminals/{terminalId}/vision/detect-sku-frame/ */
export async function detectSKUFrame(
  terminalId: string,
  checkoutSessionId: number,
): Promise<SKUDetectResult> {
  const res = await apiClient.post<SKUDetectResult>(
    `${base(terminalId)}/vision/detect-sku-frame/`,
    { checkout_session_id: checkoutSessionId },
  );
  return res.data;
}

/** POST /api/terminals/{terminalId}/vision/detect-weighted-frame/ */
export async function detectWeightedFrame(
  terminalId: string,
  checkoutSessionId: number,
): Promise<WeightedDetectResult> {
  const res = await apiClient.post<WeightedDetectResult>(
    `${base(terminalId)}/vision/detect-weighted-frame/`,
    { checkout_session_id: checkoutSessionId },
  );
  return res.data;
}
