import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as cameraApi from '../../../api/cameraApi';
import type { CameraConfig, CameraSourceType } from '../../../types/camera';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_TERMINAL_ID = 'cashier-01';

const SOURCE_LABELS: Record<CameraSourceType, string> = {
  MOCK_FOLDER: 'Mock Folder',
  USB: 'USB Camera',
  NETWORK: 'Network / IP Camera',
};

// ---------------------------------------------------------------------------
// Single camera panel
// ---------------------------------------------------------------------------

interface CameraPanelProps {
  role: 'sku' | 'weighted';
  label: string;
  icon: string;
  terminalId: string;
}

function CameraPanel({ role, label, icon, terminalId }: CameraPanelProps) {
  const [config, setConfig] = useState<CameraConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [previewKey, setPreviewKey] = useState(0); // bump to refresh preview img

  // Local form state
  const [sourceType, setSourceType] = useState<CameraSourceType>('MOCK_FOLDER');
  const [mockFolderPath, setMockFolderPath] = useState('');
  const [usbDeviceIndex, setUsbDeviceIndex] = useState<string>('0');
  const [streamUrl, setStreamUrl] = useState('');
  const [frameIntervalMs, setFrameIntervalMs] = useState<string>('1000');

  useEffect(() => {
    setLoading(true);
    cameraApi
      .getCameraSettings(terminalId, role)
      .then((cfg) => {
        setConfig(cfg);
        setSourceType(cfg.source_type);
        setMockFolderPath(cfg.mock_folder_path ?? '');
        setUsbDeviceIndex(String(cfg.usb_device_index ?? 0));
        setStreamUrl(cfg.stream_url ?? '');
        setFrameIntervalMs(String(cfg.frame_interval_ms ?? 1000));
      })
      .catch(() => setSaveError('Failed to load camera settings.'))
      .finally(() => setLoading(false));
  }, [terminalId, role]);

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    setTestResult(null);

    const payload: Partial<CameraConfig> = {
      source_type: sourceType,
      frame_interval_ms: parseInt(frameIntervalMs, 10) || 1000,
      mock_folder_path: sourceType === 'MOCK_FOLDER' ? mockFolderPath : null,
      usb_device_index: sourceType === 'USB' ? parseInt(usbDeviceIndex, 10) : null,
      stream_url: sourceType === 'NETWORK' ? streamUrl : null,
    };

    try {
      const updated = await cameraApi.updateCameraSettings(terminalId, role, payload);
      setConfig(updated);
      setSaveSuccess(true);
      setPreviewKey((k) => k + 1);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      if (data && typeof data === 'object') {
        const msgs = Object.values(data as Record<string, string[]>)
          .flat()
          .join(' ');
        setSaveError(msgs || 'Failed to save settings.');
      } else {
        setSaveError('Failed to save settings.');
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await cameraApi.testCamera(terminalId, role);
      setTestResult(result);
      if (result.ok) setPreviewKey((k) => k + 1);
    } catch {
      setTestResult({ ok: false, message: 'Test request failed.' });
    } finally {
      setTesting(false);
    }
  }

  const previewSrc = `${cameraApi.previewUrl(terminalId, role)}?t=${previewKey}`;

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center rounded-xl border border-[#e7bdb7] bg-white shadow-sm">
        <svg className="h-6 w-6 animate-spin text-[#bb0010]" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#e7bdb7] bg-white shadow-sm overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center gap-3 border-b border-[#e7bdb7] bg-[#fff0ee] px-5 py-4">
        <span className="text-2xl">{icon}</span>
        <div>
          <h2 className="text-sm font-bold text-[#291714]">{label}</h2>
          <p className="text-[11px] text-[#5d3f3c]">
            Terminal: <span className="font-mono font-semibold">{terminalId}</span>
            {' · '}
            Role: <span className="font-mono font-semibold">{config?.camera_role ?? role.toUpperCase()}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 p-5 lg:grid-cols-2">
        {/* Left: settings form */}
        <div className="flex flex-col gap-4">
          {/* Source type */}
          <div>
            <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
              Source Type
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as CameraSourceType)}
              className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
            >
              {(Object.keys(SOURCE_LABELS) as CameraSourceType[]).map((t) => (
                <option key={t} value={t}>{SOURCE_LABELS[t]}</option>
              ))}
            </select>
          </div>

          {/* Source-specific fields */}
          {sourceType === 'MOCK_FOLDER' && (
            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
                Folder Path
              </label>
              <input
                type="text"
                value={mockFolderPath}
                onChange={(e) => setMockFolderPath(e.target.value)}
                placeholder={`media/mock_camera/${role}/`}
                className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 font-mono text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
              />
              <p className="mt-1 text-[11px] text-[#926f6a]">
                Path relative to the Django backend root. Put .jpg/.png images in this folder.
              </p>
            </div>
          )}

          {sourceType === 'USB' && (
            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
                Device Index
              </label>
              <input
                type="number"
                min={0}
                value={usbDeviceIndex}
                onChange={(e) => setUsbDeviceIndex(e.target.value)}
                placeholder="0"
                className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
              />
              <p className="mt-1 text-[11px] text-[#926f6a]">
                0 = first USB camera, 1 = second, etc. Requires opencv-python on the server.
              </p>
            </div>
          )}

          {sourceType === 'NETWORK' && (
            <div>
              <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
                Stream URL
              </label>
              <input
                type="text"
                value={streamUrl}
                onChange={(e) => setStreamUrl(e.target.value)}
                placeholder="rtsp://192.168.1.100:554/stream"
                className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 font-mono text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
              />
              <p className="mt-1 text-[11px] text-[#926f6a]">
                RTSP or HTTP stream URL. Requires opencv-python on the server.
              </p>
            </div>
          )}

          {/* Frame interval */}
          <div>
            <label className="mb-1 block text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
              Frame Interval (ms)
            </label>
            <input
              type="number"
              min={100}
              value={frameIntervalMs}
              onChange={(e) => setFrameIntervalMs(e.target.value)}
              className="w-full rounded-lg border border-[#e7bdb7] bg-white px-3 py-2 text-sm focus:border-[#bb0010] focus:outline-none focus:ring-2 focus:ring-[#bb0010]/20"
            />
            <p className="mt-1 text-[11px] text-[#926f6a]">
              For mock folder: how often the image cycles (ms). Default: 1000.
            </p>
          </div>

          {/* Feedback */}
          {saveError && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {saveError}
            </div>
          )}
          {saveSuccess && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
              ✓ Settings saved successfully.
            </div>
          )}
          {testResult && (
            <div
              className={`rounded-lg border px-3 py-2 text-xs ${
                testResult.ok
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                  : 'border-red-200 bg-red-50 text-red-700'
              }`}
            >
              {testResult.ok ? '✓' : '✗'} {testResult.message}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleTest}
              disabled={testing || saving}
              className="flex flex-1 items-center justify-center gap-1 rounded-lg border border-[#bb0010] px-4 py-2 text-xs font-bold text-[#bb0010] hover:bg-red-50 disabled:opacity-40"
            >
              {testing ? (
                <>
                  <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Testing…
                </>
              ) : '🔌 Test Camera'}
            </button>
            <button
              onClick={handleSave}
              disabled={saving || testing}
              className="flex flex-1 items-center justify-center gap-1 rounded-lg bg-[#bb0010] px-4 py-2 text-xs font-bold text-white hover:brightness-110 disabled:opacity-40"
            >
              {saving ? (
                <>
                  <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Saving…
                </>
              ) : '💾 Save Settings'}
            </button>
          </div>
        </div>

        {/* Right: preview */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-bold uppercase tracking-wider text-[#5d3f3c]">
            Live Preview
          </p>
          <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-lg bg-black">
            <img
              key={previewKey}
              src={previewSrc}
              alt={`${label} preview`}
              className="h-full w-full object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            {/* Fallback overlay — shown when img fails to load */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className="text-3xl opacity-30">{icon}</span>
              <p className="mt-1 text-[10px] text-gray-500 opacity-60">
                No preview — save settings and test the camera first
              </p>
            </div>
          </div>
          <button
            onClick={() => setPreviewKey((k) => k + 1)}
            className="self-end rounded-lg border border-[#e7bdb7] px-3 py-1 text-[11px] font-semibold text-[#5d3f3c] hover:bg-[#fff0ee]"
          >
            ↻ Refresh Preview
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CameraSettingsPage() {
  const navigate = useNavigate();
  const terminalId = DEFAULT_TERMINAL_ID;

  return (
    <div className="min-h-screen bg-[#C2BFB0] font-sans text-[#291714]">
      {/* Header */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-[#e7bdb7] bg-[#fff8f7] px-6 py-3 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="rounded-lg border border-[#e7bdb7] px-3 py-1.5 text-xs font-semibold text-[#5d3f3c] hover:bg-[#fff0ee]"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-lg font-black text-[#bb0010]">Camera Settings</h1>
            <p className="text-[11px] text-[#5d3f3c]">
              Terminal: <span className="font-mono font-semibold">{terminalId}</span>
            </p>
          </div>
        </div>
        <div className="rounded-full bg-[#fff0ee] px-3 py-1 text-[11px] font-bold text-[#ab332c]">
          ⚙️ Configuration
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 p-6">
        <div className="rounded-xl border border-[#e7bdb7] bg-white/60 px-5 py-3 text-sm text-[#5d3f3c]">
          <strong>How it works:</strong> The backend owns the camera feed. React only displays the
          preview and triggers detection. Set the source type, configure the path/index/URL, save,
          then test. The cashier dashboard will use these settings automatically.
        </div>

        <CameraPanel
          role="sku"
          label="SKU Checkout Camera"
          icon="📦"
          terminalId={terminalId}
        />

        <CameraPanel
          role="weighted"
          label="Weighted Item Camera"
          icon="⚖️"
          terminalId={terminalId}
        />
      </main>
    </div>
  );
}
