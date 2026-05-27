/**
 * Format a numeric amount as Ethiopian Birr (ETB).
 * Example: formatMoney(278.25) → "278.25 ETB"
 */
export function formatMoney(amount: number, currency = 'ETB'): string {
  return `${amount.toFixed(2)} ${currency}`;
}

/**
 * Calculate subtotal for a piece-based item.
 */
export function calcSubtotal(quantity: number, unitPrice: number): number {
  return parseFloat((quantity * unitPrice).toFixed(2));
}

/**
 * Calculate subtotal for a weight-based item.
 */
export function calcWeightedSubtotal(
  weightKg: number,
  pricePerKg: number,
): number {
  return parseFloat((weightKg * pricePerKg).toFixed(2));
}

/**
 * Sum an array of subtotals.
 */
export function sumSubtotals(subtotals: number[]): number {
  return parseFloat(subtotals.reduce((acc, v) => acc + v, 0).toFixed(2));
}
