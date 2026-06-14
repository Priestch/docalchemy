import { useState, useEffect } from 'react';
import { FileText, Play, Server } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../apiClient';
import { SourceDocumentListDTO, ProviderDefinition } from '../types';

export function Dashboard() {
  const [docCount, setDocCount] = useState<number | null>(null);
  const [providerCount, setProviderCount] = useState<number | null>(null);

  useEffect(() => {
    apiClient.get<SourceDocumentListDTO>('/documents', { params: { limit: 0 } })
      .then(res => setDocCount(res.data.total))
      .catch(console.error);

    apiClient.get<ProviderDefinition[]>('/providers')
      .then(res => setProviderCount(res.data.length))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start space-x-4 mb-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider truncate">Documents</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">{docCount ?? '—'}</p>
            </div>
          </div>
          <Link to="/documents" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">View all documents &rarr;</Link>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start space-x-4 mb-4">
            <div className="p-3 bg-purple-50 text-purple-600 rounded-lg shrink-0">
              <Play className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider truncate">Analysis Runs</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">{providerCount !== null ? `—` : '—'}</p>
            </div>
          </div>
          <div className="text-sm text-gray-500">Across {providerCount ?? '—'} providers</div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-start space-x-4 mb-4">
            <div className="p-3 bg-green-50 text-green-600 rounded-lg shrink-0">
              <Server className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider truncate">Providers Online</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">{providerCount ?? '—'}</p>
            </div>
          </div>
          <Link to="/providers" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">Manage providers &rarr;</Link>
        </div>
      </div>
    </div>
  );
}
