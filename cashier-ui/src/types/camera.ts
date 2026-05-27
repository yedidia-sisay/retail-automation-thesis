// ---------------------------------------------------------------------------
// Camera types — aligned with Django CameraConfig model and serializers
// ---------------------------------------------------------------------------

export type CameraRole = 'SKU' | 'WEIGHTED';
export type CameraSourceType = 'MOCK_FOLDER' | 'USB' | 'NETWORK';

export interface CameraConfig {
  id: number;
  terminal_id: string;
  camera_role: CameraRole;
  source_type: CameraSourceType;
  is_active: boolean;
  mock_folder_path: string | null;
  usb_device_index: number | null;
  stream_url: string | null;
  snapshot_url: string | null;
  frame_interval_ms: number;
  created_at: string;
  updated_at: string;
}

export interface CameraTestResult {
  ok: boolean;
  message: string;
}

/** Shape returned by POST .../detect-sku-frame/ */
export interface SKUDetectResult {
  camera_role: 'SKU';
  source_type: CameraSourceType | null;
  detection_run_id?: number;
  status?: string;
  detections: unknown[];
  draft_items: DraftItem[];
  message: string;
}

export interface DraftItem {
  product_id: number;
  product_name: string;
  quantity: string;
  unit_price: string;
  subtotal: string;
  source: string;
  needs_review: boolean;
}

/** Shape returned by POST .../detect-weighted-frame/ */
export interface WeightedDetectResult {
  camera_role: 'WEIGHTED';
  source_type: CameraSourceType | null;
  detected_product: null | { id: number; name: string; sku: string };
  weight_value: string | null;
  weight_source: 'OCR' | 'MANUAL_REQUIRED';
  unit_price: string | null;
  subtotal: string | null;
  message: string;
}
