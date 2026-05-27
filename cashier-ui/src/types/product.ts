// ---------------------------------------------------------------------------
// Product types — aligned with Django catalog serializers
// ---------------------------------------------------------------------------

export type UnitType = 'piece' | 'kg' | 'gram';

export interface Product {
  id: number;
  name: string;
  sku: string;
  unit_type: UnitType;
  current_price: string; // decimal string
  category: number | null;
  category_name?: string;
  is_active: boolean;
  odoo_product_id: string | null;
  barcodes?: ProductBarcode[];
}

export interface ProductBarcode {
  id: number;
  barcode: string;
  product: number;
}

/** Shape returned by POST /api/vision/detect/ */
export interface VisionDetectResult {
  detection_run_id: number;
  status: string;
  detections: DetectedObject[];
  draft_items: DraftItem[];
}

export interface DetectedObject {
  id: number;
  class_name: string;
  confidence: string;
  bbox_x1: number;
  bbox_y1: number;
  bbox_x2: number;
  bbox_y2: number;
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
