import { useState, useEffect } from 'react';
import { ProviderDefinition } from '../types';
import { apiClient } from '../apiClient';
import { CheckCircle2, XCircle, Cpu } from 'lucide-react';

// Short labels keep the capability chips compact enough to wrap cleanly.
const CAPABILITY_LABELS: Record<string, string> = {
  has_ocr: 'OCR',
  has_table_extraction: 'Tables',
  has_reading_order: 'Reading Order',
  has_formula: 'Formula',
  has_image_description: 'Image Desc',
};

function formatLabel(key: string): string {
  return (
    CAPABILITY_LABELS[key] ??
    key
      .replace('has_', '')
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')
  );
}

export function Providers() {
  const [providers, setProviders] = useState<ProviderDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProviders = async () => {
      try {
        const res = await apiClient.get<ProviderDefinition[]>('/providers');
        setProviders(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadProviders();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Analysis Providers</h2>
        <p className="text-sm text-gray-500">Available engines for document extraction and analysis.</p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading providers...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {providers.map((provider) => (
            <div
              key={provider.provider_id}
              className="bg-white border border-gray-200 rounded-xl shadow-sm p-5"
            >
              {/* Header: brand accent + name + version, with a hairline divider
                  that restores the two-section feel without a heavy gray block. */}
              <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 shrink-0">
                  <Cpu className="w-4 h-4" />
                </div>
                <h3 className="flex-1 min-w-0 text-base font-medium text-gray-900 truncate">
                  {provider.display_name}
                </h3>
                <span className="text-xs text-gray-400 shrink-0">v{provider.version}</span>
              </div>

              {/* Capabilities: lighter chips (no ring) — enabled pop, disabled recede. */}
              <div className="flex flex-wrap gap-1.5 pt-3">
                {Object.entries(provider.capabilities).map(([key, value]) => (
                  <span
                    key={key}
                    className={
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs ' +
                      (value
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-gray-50 text-gray-400')
                    }
                  >
                    {value ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      <XCircle className="w-3 h-3" />
                    )}
                    {formatLabel(key)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
