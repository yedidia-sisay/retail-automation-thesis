export type UnitType = 'piece' | 'kg' | 'gram';

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string | null;
  unitType: UnitType;
  currentPrice: number;
  category: string | null;
  isActive: boolean;
  odoProductId: string | null;
}

export interface DetectedProduct {
  id: string;
  product: Product | null;
  detectedClass: string;
  confidence: number;
  quantity: number;
  unitPrice: number;
  subtotal: number;
  status: 'suggested' | 'needs_review' | 'unknown' | 'accepted' | 'rejected';
  source: 'vision' | 'barcode' | 'manual' | 'weighted';
}

export interface WeightedItemCandidate {
  product: Product | null;
  detectedClass: string;
  confidence: number;
  weight: number;
  weightSource: 'ocr' | 'manual' | 'scale_service';
  unitPricePerKg: number;
  subtotal: number;
}
