import { useState, useEffect } from 'react';
import { ProviderDefinition } from '../types';
import { apiClient } from '../apiClient';
import { Settings, CheckCircle2, XCircle } from 'lucide-react';

export function Providers() {
  const [providers, setProviders] = useState<ProviderDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProviders = async () => {
      try {
        const res = await apiClient.get<ProviderDefinition[]>('/providers');
        setProviders(res.data);
      } catch(e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadProviders();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Analysis Providers</h2>
        <p className="text-sm text-gray-500">Available engines for document extraction and analysis.</p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading providers...</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {providers.map(provider => (
            <div key={provider.provider_id} className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{provider.display_name}</h3>
                  <p className="text-xs text-gray-500 mt-1">Version {provider.version}</p>
                </div>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Settings className="w-5 h-5" />
                </div>
              </div>
              <div className="p-6 bg-gray-50 flex-1">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Capabilities</h4>
                <ul className="space-y-2">
                  {Object.entries(provider.capabilities).map(([key, value]) => (
                    <li key={key} className="flex items-center text-sm">
                      {value ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
                      ) : (
                        <XCircle className="w-4 h-4 text-gray-300 mr-2" />
                      )}
                      <span className={value ? "text-gray-700" : "text-gray-400"}>
                        {key.replace('has_', '').split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
