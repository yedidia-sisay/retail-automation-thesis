import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import * as checkoutApi from '../../../api/checkoutApi';
import { useAuth } from '../../../store/authContext';
import { getFullName } from '../../../types/auth';
import type { CheckoutSession, CheckoutItem } from '../../../types/checkout';

function fmt(v: string | number | null | undefined) {
  return parseFloat(String(v ?? 0)).toFixed(2);
}
function confidencePct(v: string | null) {
  if (!v) return '';
  return `${Math.round(parseFloat(v) * 100)}%`;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; dot: string; label: string }> = {
    OPEN: { bg: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500', label: 'Open' },
    CONFIRMED: { bg: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500', label: 'Confirmed' },
    PAYMENT_PENDING: { bg: 'bg-yellow-100 text-yellow-700', dot: 'bg-yellow-500', label: 'Payment Pending' },
    COMPLETED: { bg: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400', label: 'Completed' },
    CANCELLED: { bg: 'bg-red-100 text-red-600', dot: 'bg-red-400', label: 'Cancelled' },
  };
  const s = map[status] ?? map.OPEN;
  return (
    <span className={`flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-bold uppercase ${s.bg}`}>
      <span className={`h-2 w-2 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const map: Record<string, string> = {
    VISION: 'bg-purple-100 text-purple-700',
    BARCODE: 'bg-blue-100 text-blue-700',
    MANUAL: 'bg-gray-100 text-gray-600',
    WEIGHTED: 'bg-sky-100 text-sky-700',
  };
  return (
    <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${map[source] ?? 'bg-gray-100 text-gray-500'}`}>
      {source}
    </span>
  );
}

interface ItemCardProps {
  item: CheckoutItem;
  busy: boolean;
  isEditable: boolean;
  onAccept: (item: CheckoutItem) => void;
  onReject: (item: CheckoutItem) => void;
  onRemove: (item: CheckoutItem) => void;
  onQtyChange: (item: CheckoutItem, qty: string) => void;
}

function ItemCard({ item, busy, isEditable, onAccept, onReject, onRemove, onQtyChange }: ItemCardProps) {
  const needsReview = item.review_status === 'NEEDS_REVIEW' || item.status === 'NEEDS_REVIEW';
  const isRejected = item.review_status === 'REJECTED' || item.status === 'REMOVED';
  const confidence = item.confidence ? confidencePct(item.confidence) : null;
  const border = needsReview
    ? 'border-2 border-yellow-400'
    : isRejected
    ? 'border border-red-200 opacity-50'
    : 'border border-[#e7bdb7] hover:border-[#bb0010]/40';

  return (
    <div className={`flex items-center justify-between rounded-xl bg-white px-4 py-3 shadow-sm transition-all ${border}`}>
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold text-[#291714]">{item.product_name}</span>
          <SourceBadge source={item.source} />
        </div>
        <div className="flex items-center gap-2 text-xs text-[#5d3f3c]">
          {confidence && (
            <span className={needsReview ? 'font-bold text-yellow-600' : 'font-bold text-emerald-600'}>
              {confidence}{needsReview ? ' — Review Required' : ' Confidence'}
            </span>
          )}
          <span>{item.unit_type === 'kg' ? `${fmt(item.quantity)} kg` : `Qty ${fmt(item.quantity)}`}</span>
          <span>×</span>
          <span>{fmt(item.unit_price)} ETB</span>
          <span>=</span>
          <span className="font-bold">{fmt(item.subtotal)} ETB</span>
        </div>
      </div>
      {isEditable && !isRejected && (
        <div className="flex items-center gap-2">
          <select
            value={String(Math.round(parseFloat(item.quantity)))}
            onChange={(e) => onQtyChange(item, e.target.value)}
            disabled={busy}
            className="rounded-lg border-none bg-[#fff0ee] px-3 py-1.5 text-sm font-bold focus:ring-0"
          >
            {[1,2,3,4,5,6,7,8,9,10].map((n) => (
              <option key={n} value={n}>{n} {item.unit_type === 'kg' ? 'kg' : 'Qty'}</option>
            ))}
          </select>
          {['NEEDS_REVIEW','NOT_REQUIRED'].includes(item.review_status) && (
            <button onClick={() => onAccept(item)} disabled={busy}
              className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-white hover:brightness-110 disabled:opacity-40">
              {busy ? '…' : 'Accept'}
            </button>
          )}
          {item.review_status !== 'REJECTED' && (
            <button onClick={() => onReject(item)} disabled={busy} title="Reject"
              className="rounded-lg p-1.5 text-[#ba1a1a] hover:bg-red-50 disabled:opacity-40">✕</button>
          )}
          <button onClick={() => onRemove(item)} disabled={busy} title="Remove"
            className="rounded-lg p-1.5 text-[#ba1a1a] hover:bg-red-50 disabled:opacity-40">🗑</button>
        </div>
      )}
    </div>
  );
}

export function CheckoutSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [barcodeInput, setBarcodeInput] = useState('');
  const [barcodeLoading, setBarcodeLoading] = useState(false);
  const [barcodeError, setBarcodeError] = useState<string | null>(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(
    new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
  );

  useEffect(() => {
    const t = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
    }, 30_000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    checkoutApi.getSession(Number(sessionId))
      .then(setSession)
      .catch(() => setPageError('Failed to load checkout session.'))
      .finally(() => setLoading(false));
  }, [sessionId]);

  async function handleAccept(item: CheckoutItem) {
    setActionLoading(item.id);
    try {
      const u = await checkoutApi.acceptItem(item.id);
      setSession((s) => s ? { ...s, items: s.items.map((i) => i.id === u.id ? u : i) } : s);
    } finally { setActionLoading(null); }
  }

  async function handleReject(item: CheckoutItem) {
    setActionLoading(item.id);
    try {
      const u = await checkoutApi.rejectItem(item.id);
      setSession((s) => s ? { ...s, items: s.items.map((i) => i.id === u.id ? u : i) } : s);
    } finally { setActionLoading(null); }
  }

  async function handleRemove(item: CheckoutItem) {
    setActionLoading(item.id);
    try {
      const u = await checkoutApi.removeItem(item.id);
      setSession((s) => s ? { ...s, items: s.items.map((i) => i.id === u.id ? u : i) } : s);
    } finally { setActionLoading(null); }
  }

  async function handleQtyChange(item: CheckoutItem, qty: string) {
    if (!qty || parseFloat(qty) <= 0) return;
    setActionLoading(item.id);
    try {
      const u = await checkoutApi.changeItemQuantity(item.id, qty);
      setSession((s) => s ? { ...s, items: s.items.map((i) => i.id === u.id ? u : i) } : s);
    } finally { setActionLoading(null); }
  }

  async function handleBarcodeAdd(e: FormEvent) {
    e.preventDefault();
    const code = barcodeInput.trim();
    if (!code) return;
    setBarcodeLoading(true);
    setBarcodeError(null);
    try {
      const updated = await checkoutApi.addBarcodeItem(Number(sessionId), code);
      setSession(updated);
      setBarcodeInput('');
    } catch {
      setBarcodeError('Barcode not found or could not be added.');
    } finally { setBarcodeLoading(false); }
  }

  async function handleConfirm() {
    if (!session) return;
    setConfirmLoading(true);
    setPageError(null);
    try {
      await checkoutApi.confirmSession(session.id);
      const refreshed = await checkoutApi.getSession(session.id);
      setSession(refreshed);
      if (refreshed.receipt_id) navigate(`/receipts/${refreshed.receipt_id}`);
    } catch {
      setPageError('Failed to confirm. Make sure all items needing review are accepted or rejected.');
    } finally { setConfirmLoading(false); }
  }

  async function handleCancel() {
    if (!session) return;
    setCancelLoading(true);
    try {
      await checkoutApi.cancelSession(session.id);
      navigate('/cashier/dashboard');
    } catch {
      setPageError('Failed to cancel session.');
    } finally { setCancelLoading(false); }
  }

  const isEditable = session?.status === 'OPEN';
  const activeItems = session?.items.filter((i) => i.status !== 'REMOVED') ?? [];
  const visionItems = activeItems.filter((i) => i.source === 'VISION');
  const nonVisionItems = activeItems.filter((i) => i.source !== 'VISION');
  const cashierName = user ? getFullName(user) : (session?.cashier_username ?? '—');
  const subtotal = activeItems.reduce((sum, i) => sum + parseFloat(i.subtotal), 0);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#C2BFB0]">
        <div className="flex flex-col items-center gap-3">
          <svg className="h-8 w-8 animate-spin text-[#bb0010]" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <p className="text-sm text-[#5d3f3c]">Loading session…</p>
        </div>
      </div>
    );
  }

  if (pageError && !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#C2BFB0]">
        <div className="rounded-xl bg-white p-8 text-center shadow">
          <p className="text-red-600">{pageError}</p>
          <button onClick={() => navigate('/cashier/dashboard')}
            className="mt-4 rounded-lg bg-[#bb0010] px-4 py-2 text-sm text-white">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#C2BFB0] font-sans text-[#291714]">

      {/* ── Header ── */}
      <header className="fixed left-0 right-0 top-0 z-50 flex items-center justify-between border-b border-[#e7bdb7] bg-[#fff8f7] px-6 py-3 shadow-sm">
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-2xl font-black tracking-tight text-[#bb0010]">VisionPOS AI</span>
            <span className="text-[11px] font-bold uppercase tracking-widest text-[#5d3f3c]">Session #{session?.id ?? '—'}</span>
          </div>
          <div className="mx-2 h-8 w-px bg-[#e7bdb7]" />
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#ab332c]">Cashier</span>
              <span className="text-base font-semibold">{cashierName}</span>
            </div>
            <StatusBadge status={session?.status ?? 'OPEN'} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-[#5d3f3c]">{currentTime}</span>
          <button onClick={() => navigate('/cashier/dashboard')}
            className="flex items-center gap-1 rounded-lg bg-[#bb0010] px-4 py-2 text-xs font-bold text-white hover:brightness-110 active:scale-95 transition-all">
            + New Session
          </button>
          <button onClick={handleCancel} disabled={cancelLoading || !isEditable}
            className="flex items-center gap-1 rounded-lg border border-[#ba1a1a] px-4 py-2 text-xs font-bold text-[#ba1a1a] hover:bg-red-50 active:scale-95 transition-all disabled:opacity-40">
            {cancelLoading ? '…' : 'Cancel Session'}
          </button>
        </div>
      </header>

      {/* ── 3-column grid ── */}
      <main className="mt-[64px] grid h-[calc(100vh-64px)] grid-cols-12 gap-4 overflow-hidden p-4">

        {/* LEFT: Camera Feeds */}
        <section className="col-span-3 flex h-full flex-col gap-4">
          <div className="flex flex-1 flex-col gap-2">
            <div className="relative flex-1 overflow-hidden rounded-xl bg-black">
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div className="mb-2 text-4xl">📦</div>
                  <p className="text-xs text-gray-400">Packaged Product Feed</p>
                  <p className="mt-1 text-[10px] text-gray-500">Camera — Phase 4</p>
                </div>
              </div>
              <div className="absolute bottom-3 left-3">
                <span className="animate-pulse rounded bg-red-500 px-2 py-0.5 text-[10px] font-bold uppercase text-white">Live</span>
              </div>
            </div>
            <button disabled={!isEditable}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#bb0010] py-3 text-xs font-bold text-white hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-40">
              📷 Capture Packaged
            </button>
          </div>
          <div className="flex flex-1 flex-col gap-2">
            <div className="relative flex-1 overflow-hidden rounded-xl bg-black">
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div className="mb-2 text-4xl">⚖️</div>
                  <p className="text-xs text-gray-400">Weighted Scale Feed</p>
                  <p className="mt-1 text-[10px] text-gray-500">One item at a time</p>
                </div>
              </div>
              <div className="absolute left-3 top-3 rounded-lg border border-white/10 bg-black/60 px-3 py-1.5 font-mono text-sm text-white backdrop-blur-md">
                0.00 kg
              </div>
            </div>
            <button disabled={!isEditable}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#ff7164] py-3 text-xs font-bold text-[#700408] hover:brightness-105 active:scale-[0.98] transition-all disabled:opacity-40">
              ⚖️ Capture Weighted
            </button>
          </div>
        </section>

        {/* MIDDLE: Review */}
        <section className="col-span-6 flex h-full flex-col gap-3 overflow-y-auto pr-1">
          {pageError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{pageError}</div>
          )}

          {/* Vision items */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <h3 className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#ab332c]">Packaged Detection</h3>
              {visionItems.length > 0 && isEditable && (
                <button
                  onClick={() => Promise.all(
                    visionItems.filter((i) => ['NEEDS_REVIEW','NOT_REQUIRED'].includes(i.review_status)).map(handleAccept)
                  )}
                  className="rounded-xl bg-emerald-500 px-5 py-2 text-[11px] font-bold text-white shadow hover:brightness-110 active:scale-95 transition-all">
                  Accept All Matches
                </button>
              )}
            </div>
            {visionItems.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#e7bdb7] bg-white/50 py-8 text-center text-xs text-[#926f6a]">
                No packaged detections yet. Capture an image to detect products.
              </div>
            ) : (
              visionItems.map((item) => (
                <ItemCard key={item.id} item={item} busy={actionLoading === item.id}
                  isEditable={isEditable} onAccept={handleAccept} onReject={handleReject}
                  onRemove={handleRemove} onQtyChange={handleQtyChange} />
              ))
            )}
          </div>

          {/* Non-vision items */}
          {nonVisionItems.length > 0 && (
            <div className="space-y-3">
              <h3 className="px-1 text-[11px] font-bold uppercase tracking-[0.2em] text-[#ab332c]">Added Items</h3>
              {nonVisionItems.map((item) => (
                <ItemCard key={item.id} item={item} busy={actionLoading === item.id}
                  isEditable={isEditable} onAccept={handleAccept} onReject={handleReject}
                  onRemove={handleRemove} onQtyChange={handleQtyChange} />
              ))}
            </div>
          )}

          {/* Barcode fallback */}
          {isEditable && (
            <div className="mt-auto space-y-3 pt-4">
              <form onSubmit={handleBarcodeAdd} className="flex gap-2">
                <div className="relative flex-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#926f6a] text-sm">🔍</span>
                  <input value={barcodeInput} onChange={(e) => setBarcodeInput(e.target.value)}
                    disabled={barcodeLoading} placeholder="Scan or enter barcode…"
                    className="w-full rounded-xl border border-[#e7bdb7] bg-white py-2.5 pl-9 pr-4 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20" />
                </div>
                <button type="submit" disabled={barcodeLoading}
                  className="rounded-xl bg-[#bb0010] px-5 text-xs font-bold text-white hover:brightness-110 disabled:opacity-40">
                  {barcodeLoading ? '…' : 'Add'}
                </button>
              </form>
              {barcodeError && <p className="text-xs text-red-600">{barcodeError}</p>}
            </div>
          )}
        </section>

        {/* RIGHT: Receipt + Payment */}
        <section className="col-span-3 flex h-full flex-col gap-3">
          {/* Receipt preview */}
          <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-[#e7bdb7] bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-[#e7bdb7] bg-[#fff0ee] px-4 py-3">
              <h2 className="text-sm font-semibold text-[#291714]">Receipt Preview</h2>
              <span className="text-[10px] font-bold uppercase text-yellow-600">
                {session?.receipt_payment_status ?? 'Pending'}
              </span>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {activeItems.length === 0 ? (
                <p className="text-center text-xs text-[#926f6a]">No items added yet.</p>
              ) : (
                activeItems.map((item) => (
                  <div key={item.id} className="flex items-start justify-between text-sm">
                    <div className="flex flex-col">
                      <span className="font-semibold">{item.product_name}</span>
                      <span className="text-[11px] text-[#5d3f3c]">
                        {item.unit_type === 'kg'
                          ? `${fmt(item.quantity)} kg @ ${fmt(item.unit_price)}`
                          : `${fmt(item.quantity)} × ${fmt(item.unit_price)}`}
                      </span>
                    </div>
                    <span className="font-bold">{fmt(item.subtotal)}</span>
                  </div>
                ))
              )}
            </div>
            <div className="border-t border-dashed border-[#e7bdb7] bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase">Total</span>
                <span className="text-lg font-black text-[#bb0010]">{subtotal.toFixed(2)} ETB</span>
              </div>
            </div>
          </div>

          {/* Payment panel */}
          <div className="space-y-3 rounded-xl border border-[#e7bdb7] bg-white p-4 shadow-sm">
            <select className="w-full rounded-lg border border-[#e7bdb7] bg-[#fff0ee] px-3 py-2.5 text-sm font-semibold focus:ring-[#bb0010]">
              <option>Cash Payment</option>
              <option>Mobile Money</option>
              <option>Card Payment</option>
              <option>Telebirr</option>
            </select>
            <button
              onClick={handleConfirm}
              disabled={confirmLoading || !isEditable || activeItems.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#bb0010] py-4 text-xs font-bold text-white shadow-lg hover:brightness-110 active:scale-95 transition-all disabled:opacity-40">
              {confirmLoading ? 'Processing…' : 'Complete Transaction →'}
            </button>
          </div>
        </section>
      </main>

      {/* Bottom accent bar */}
      <footer className="fixed bottom-0 left-0 right-0 h-1.5 bg-[#bb0010]/20" />
    </div>
  );
}

export default CheckoutSessionPage;
