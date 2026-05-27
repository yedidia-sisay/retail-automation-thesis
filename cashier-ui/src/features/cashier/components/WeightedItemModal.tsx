import { useState, type FormEvent } from 'react';
import { addWeightedItem, getSession } from '../../../api/checkoutApi';
import { ProductSearchModal } from './ProductSearchModal';
import type { Product } from '../../../types/product';
import type { CheckoutSession } from '../../../types/checkout';

interface Props {
  sessionId: number;
  onAdded: (updatedSession: CheckoutSession) => void;
  onClose: () => void;
}

export function WeightedItemModal({ sessionId, onAdded, onClose }: Props) {
  const [step, setStep] = useState<'search' | 'weight'>('search');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [weight, setWeight] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleProductSelect(product: Product) {
    setSelectedProduct(product);
    setStep('weight');
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedProduct || !weight || parseFloat(weight) <= 0) {
      setError('Enter a valid weight.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const weightUnit = selectedProduct.unit_type === 'gram' ? 'GRAM' : 'KG';
      await addWeightedItem(sessionId, selectedProduct.id, weight, weightUnit, 'MANUAL');
      const updated = await getSession(sessionId);
      onAdded(updated);
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to add weighted item.');
    } finally {
      setLoading(false);
    }
  }

  if (step === 'search') {
    return (
      <ProductSearchModal
        title="Select Weighted Product"
        weightedOnly
        onSelect={handleProductSelect}
        onClose={onClose}
      />
    );
  }

  // Step: enter weight
  const unitLabel = selectedProduct?.unit_type === 'gram' ? 'g' : 'kg';
  const unitPrice = selectedProduct ? parseFloat(selectedProduct.current_price) : 0;
  const weightNum = parseFloat(weight) || 0;
  const subtotal = (weightNum * unitPrice).toFixed(2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#e7bdb7] px-5 py-4">
          <h2 className="text-base font-bold text-[#291714]">Add Weighted Item</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-[#5d3f3c] hover:bg-[#fff0ee]">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-5 py-4">
          {/* Selected product */}
          <div className="rounded-xl border border-[#e7bdb7] bg-[#fff0ee] px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-[#291714]">{selectedProduct?.name}</p>
                <p className="text-xs text-[#5d3f3c]">
                  {unitPrice.toFixed(2)} ETB / {unitLabel}
                </p>
              </div>
              <button
                type="button"
                onClick={() => { setStep('search'); setWeight(''); setError(null); }}
                className="text-xs text-[#bb0010] underline"
              >
                Change
              </button>
            </div>
          </div>

          {/* Weight input */}
          <div>
            <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
              Weight ({unitLabel})
            </label>
            <input
              autoFocus
              type="number"
              step="0.001"
              min="0.001"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder={`e.g. 1.350`}
              className="w-full rounded-xl border border-[#e7bdb7] bg-white px-4 py-2.5 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
            />
          </div>

          {/* Subtotal preview */}
          {weightNum > 0 && (
            <div className="flex items-center justify-between rounded-xl bg-[#fff0ee] px-4 py-2.5">
              <span className="text-xs text-[#5d3f3c]">Subtotal</span>
              <span className="text-base font-black text-[#bb0010]">{subtotal} ETB</span>
            </div>
          )}

          {error && <p className="text-xs text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading || !weight || parseFloat(weight) <= 0}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#bb0010] py-3 text-sm font-bold text-white hover:brightness-110 disabled:opacity-40"
          >
            {loading ? (
              <>
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Adding…
              </>
            ) : 'Add to Receipt'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default WeightedItemModal;
