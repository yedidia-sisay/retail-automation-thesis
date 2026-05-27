import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getReceiptPrintPreview } from '../../../api/receiptsApi';
import type { Receipt } from '../../../types/receipt';

function fmt(v: string | number | null | undefined) {
  return parseFloat(String(v ?? 0)).toFixed(2);
}

export function PrintReceiptPage() {
  const { receiptId } = useParams<{ receiptId: string }>();
  const [receipt, setReceipt] = useState<(Receipt & { printable_text?: string }) | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!receiptId) return;
    getReceiptPrintPreview(Number(receiptId))
      .then(setReceipt)
      .finally(() => setLoading(false));
  }, [receiptId]);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center"><p className="text-sm text-gray-500">Loading…</p></div>;
  }

  if (!receipt) {
    return <div className="flex min-h-screen items-center justify-center"><p className="text-red-600">Receipt not found.</p></div>;
  }

  return (
    <div className="min-h-screen bg-white p-8 font-mono text-sm text-gray-900 print:p-4">
      <div className="mx-auto max-w-xs">
        {/* Print button — hidden during actual print */}
        <div className="mb-6 flex justify-end print:hidden">
          <button
            onClick={() => window.print()}
            className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-bold text-white hover:bg-gray-700"
          >
            🖨 Print
          </button>
        </div>

        {/* Receipt content */}
        <div className="space-y-1 text-center">
          <p className="text-lg font-bold">VisionPOS</p>
          <p className="text-xs text-gray-500">AI Retail Checkout System</p>
        </div>

        <div className="my-3 border-t border-dashed border-gray-400" />

        <div className="space-y-0.5 text-xs">
          <p>Receipt: {receipt.receipt_number}</p>
          <p>Date: {new Date(receipt.created_at).toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' })}</p>
        </div>

        <div className="my-3 border-t border-dashed border-gray-400" />

        {/* Line items */}
        <div className="space-y-2">
          {receipt.lines.map((line) => (
            <div key={line.id} className="flex justify-between text-xs">
              <div>
                <p className="font-semibold">{line.product_name}</p>
                <p className="text-gray-500">
                  {line.source === 'WEIGHTED'
                    ? `${fmt(line.quantity)}kg @ ${fmt(line.unit_price)}`
                    : `${fmt(line.quantity)} x ${fmt(line.unit_price)}`}
                </p>
              </div>
              <p className="font-bold">{fmt(line.subtotal)}</p>
            </div>
          ))}
        </div>

        <div className="my-3 border-t border-dashed border-gray-400" />

        <div className="flex justify-between font-bold">
          <span>TOTAL</span>
          <span>{fmt(receipt.total)} ETB</span>
        </div>

        <div className="my-1 flex justify-between text-xs">
          <span>Payment</span>
          <span>{receipt.payment_status}</span>
        </div>

        <div className="my-3 border-t border-dashed border-gray-400" />

        <p className="text-center text-[10px] text-gray-400">Thank you for shopping with us.</p>
      </div>
    </div>
  );
}

export default PrintReceiptPage;
