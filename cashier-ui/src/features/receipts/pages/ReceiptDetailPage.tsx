import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getReceipt } from '../../../api/receiptsApi';
import { simulatePayment } from '../../../api/paymentsApi';
import type { Receipt } from '../../../types/receipt';

function fmt(v: string | number | null | undefined) {
  return parseFloat(String(v ?? 0)).toFixed(2);
}

function PaymentStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-700',
    PAID: 'bg-emerald-100 text-emerald-700',
    FAILED: 'bg-red-100 text-red-700',
    CANCELLED: 'bg-gray-100 text-gray-600',
  };
  return (
    <span className={`rounded-full px-3 py-1 text-[11px] font-bold uppercase ${map[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
}

export function ReceiptDetailPage() {
  const { receiptId } = useParams<{ receiptId: string }>();
  const navigate = useNavigate();

  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'CASH' | 'CARD' | 'MOBILE_MONEY' | 'TELEBIRR'>('CASH');

  useEffect(() => {
    if (!receiptId) return;
    setLoading(true);
    getReceipt(Number(receiptId))
      .then(setReceipt)
      .catch(() => setError('Failed to load receipt.'))
      .finally(() => setLoading(false));
  }, [receiptId]);

  async function handleSimulatePayment() {
    if (!receipt) return;
    setPaymentLoading(true);
    setPaymentError(null);
    try {
      await simulatePayment({
        receipt_id: receipt.id,
        method: paymentMethod,
        status: 'COMPLETED',
        amount: receipt.total,
      });
      // Refresh receipt
      const updated = await getReceipt(receipt.id);
      setReceipt(updated);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setPaymentError(msg ?? 'Payment simulation failed.');
    } finally {
      setPaymentLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#C2BFB0]">
        <svg className="h-8 w-8 animate-spin text-[#bb0010]" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      </div>
    );
  }

  if (error || !receipt) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#C2BFB0]">
        <div className="rounded-xl bg-white p-8 text-center shadow">
          <p className="text-red-600">{error ?? 'Receipt not found.'}</p>
          <button onClick={() => navigate('/cashier/dashboard')}
            className="mt-4 rounded-lg bg-[#bb0010] px-4 py-2 text-sm text-white">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isPaid = receipt.payment_status === 'PAID';

  return (
    <div className="min-h-screen bg-[#C2BFB0] p-6 font-sans">
      <div className="mx-auto max-w-2xl">

        {/* Back button */}
        <button onClick={() => navigate('/cashier/dashboard')}
          className="mb-4 flex items-center gap-1 text-sm text-[#5d3f3c] hover:text-[#bb0010]">
          ← Back to Dashboard
        </button>

        {/* Receipt card */}
        <div className="overflow-hidden rounded-2xl bg-white shadow-lg">
          {/* Header */}
          <div className="border-b border-[#e7bdb7] bg-[#fff0ee] px-6 py-5">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-black text-[#bb0010]">VisionPOS</h1>
                <p className="text-sm text-[#5d3f3c]">Receipt #{receipt.receipt_number}</p>
                <p className="text-xs text-[#926f6a]">
                  {new Date(receipt.created_at).toLocaleString('en-US', {
                    dateStyle: 'medium', timeStyle: 'short',
                  })}
                </p>
              </div>
              <PaymentStatusBadge status={receipt.payment_status} />
            </div>
          </div>

          {/* Line items */}
          <div className="divide-y divide-[#e7bdb7] px-6">
            {receipt.lines.map((line) => (
              <div key={line.id} className="flex items-center justify-between py-3">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-[#291714]">{line.product_name}</span>
                  <span className="text-xs text-[#5d3f3c]">
                    {line.source === 'WEIGHTED'
                      ? `${fmt(line.quantity)} kg @ ${fmt(line.unit_price)} ETB/kg`
                      : `${fmt(line.quantity)} × ${fmt(line.unit_price)} ETB`}
                  </span>
                </div>
                <span className="font-bold text-[#291714]">{fmt(line.subtotal)} ETB</span>
              </div>
            ))}
          </div>

          {/* Total */}
          <div className="border-t-2 border-dashed border-[#e7bdb7] px-6 py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-black uppercase text-[#291714]">Total</span>
              <span className="text-2xl font-black text-[#bb0010]">{fmt(receipt.total)} ETB</span>
            </div>
          </div>

          {/* Payment section */}
          {!isPaid && (
            <div className="border-t border-[#e7bdb7] bg-[#fff8f7] px-6 py-4 space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">Simulate Payment</p>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value as typeof paymentMethod)}
                className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 text-sm font-semibold"
              >
                <option value="CASH">Cash</option>
                <option value="MOBILE_MONEY">Mobile Money</option>
                <option value="CARD">Card</option>
                <option value="TELEBIRR">Telebirr</option>
              </select>
              {paymentError && <p className="text-xs text-red-600">{paymentError}</p>}
              <button
                onClick={handleSimulatePayment}
                disabled={paymentLoading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#bb0010] py-3 text-sm font-bold text-white hover:brightness-110 disabled:opacity-40"
              >
                {paymentLoading ? 'Processing…' : `Simulate Payment — ${fmt(receipt.total)} ETB`}
              </button>
            </div>
          )}

          {isPaid && (
            <div className="border-t border-[#e7bdb7] bg-emerald-50 px-6 py-4 text-center">
              <p className="text-sm font-bold text-emerald-700">✓ Payment Completed</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 border-t border-[#e7bdb7] px-6 py-4">
            <button
              onClick={() => navigate(`/receipts/${receipt.id}/print`)}
              className="flex-1 rounded-xl border border-[#e7bdb7] py-2.5 text-sm font-bold text-[#291714] hover:bg-[#fff0ee]"
            >
              🖨 Print Preview
            </button>
            <button
              onClick={() => navigate('/cashier/dashboard')}
              className="flex-1 rounded-xl bg-[#bb0010] py-2.5 text-sm font-bold text-white hover:brightness-110"
            >
              New Checkout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReceiptDetailPage;
