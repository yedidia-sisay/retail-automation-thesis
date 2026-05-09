import { apiClient } from './client';
import type { Product } from '../types/product';

/**
 * GET /api/catalog/products/search/?q=
 * Searches products by name, SKU, barcode, or category.
 */
export async function searchProducts(query: string): Promise<Product[]> {
  const res = await apiClient.get<Product[] | { results: Product[] }>(
    '/api/catalog/products/search/',
    { params: { q: query } },
  );
  // Handle both paginated and non-paginated responses
  const data = res.data;
  if (Array.isArray(data)) return data;
  if ('results' in data) return data.results;
  return [];
}

/**
 * GET /api/catalog/products/
 * Returns all active products (for weighted item selection).
 */
export async function listProducts(): Promise<Product[]> {
  const res = await apiClient.get<Product[] | { results: Product[] }>(
    '/api/catalog/products/',
  );
  const data = res.data;
  if (Array.isArray(data)) return data;
  if ('results' in data) return data.results;
  return [];
}
