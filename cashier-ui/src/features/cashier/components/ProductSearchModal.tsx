import { useState, useEffect, type FormEvent } from 'react';
import { searchProducts } from '../../../api/catalogApi';
import type { Product } from '../../../types/product';

interface Props {
  title?: string;
  /** Filter to only weight-sold products (kg/gram) */
  weightedOnly?: boolean;
  onSelect: (product: Product) => void;
  onClose: () => void;
}

export function ProductSearchModal({ title = 'Search Product', weightedOnly = false, onSelect, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.trim().length < 2) { setResults([]); return; }
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const all = await searchProducts(query.trim());
        setResults(weightedOnly ? all.filter((p) => p.unit_type === 'kg' || p.unit_type === 'gram') : all);
      } catch {
        setError('Search failed. Try again.');
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, weightedOnly]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#e7bdb7] px-5 py-4">
          <h2 className="text-base font-bold text-[#291714]">{title}</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-[#5d3f3c] hover:bg-[#fff0ee]">✕</button>
        </div>

        {/* Search input */}
        <div className="px-5 pt-4">
          <form onSubmit={handleSubmit}>
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name, SKU, or barcode…"
              className="w-full rounded-xl border border-[#e7bdb7] bg-[#fff8f7] px-4 py-2.5 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
            />
          </form>
        </div>

        {/* Results */}
        <div className="max-h-72 overflow-y-auto px-5 py-3">
          {loading && (
            <p className="py-4 text-center text-xs text-[#926f6a]">Searching…</p>
          )}
          {error && (
            <p className="py-4 text-center text-xs text-red-600">{error}</p>
          )}
          {!loading && !error && query.trim().length >= 2 && results.length === 0 && (
            <p className="py-4 text-center text-xs text-[#926f6a]">No products found.</p>
          )}
          {!loading && results.map((product) => (
            <button
              key={product.id}
              onClick={() => onSelect(product)}
              className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left hover:bg-[#fff0ee] transition-colors"
            >
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-[#291714]">{product.name}</span>
                <span className="text-[11px] text-[#5d3f3c]">
                  SKU: {product.sku} · {product.unit_type} · {parseFloat(product.current_price).toFixed(2)} ETB
                </span>
              </div>
              <span className="ml-3 rounded-full bg-[#bb0010]/10 px-2 py-0.5 text-[10px] font-bold uppercase text-[#bb0010]">
                {product.unit_type}
              </span>
            </button>
          ))}
          {query.trim().length < 2 && (
            <p className="py-4 text-center text-xs text-[#926f6a]">Type at least 2 characters to search.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductSearchModal;
