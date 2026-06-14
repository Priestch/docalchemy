import { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { PdfViewer } from '../components/PdfViewer';
import { apiClient } from '../apiClient';
import { AnalysisRunDTO, ProviderDefinition } from '../types';
import { ArrowLeft } from 'lucide-react';

export function ComparisonDetail() {
  const { docId } = useParams<{ docId: string }>();
  const [searchParams] = useSearchParams();
  const runIds = searchParams.get('runs')?.split(',').filter(Boolean) || [];

  const [docName, setDocName] = useState<string>('');
  const [providers, setProviders] = useState<ProviderDefinition[]>([]);
  const [runs, setRuns] = useState<AnalysisRunDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncedScroll, setSyncedScroll] = useState<number | undefined>(undefined);
  const sharedPluginsRef = useRef<any[]>([]);

  useEffect(() => {
    sharedPluginsRef.current = [];
    if (!docId || runIds.length === 0) { setLoading(false); return; }

    const load = async () => {
      try {
        const [docRes, provRes, runsRes] = await Promise.all([
          apiClient.get(`/documents/${docId}`),
          apiClient.get<ProviderDefinition[]>('/providers'),
          apiClient.get<AnalysisRunDTO[]>(`/documents/${docId}/analysis-runs`),
        ]);
        setDocName(docRes.data.name);
        setProviders(provRes.data);

        const selectedRuns = runsRes.data.filter(r => runIds.includes(r.id));
        setRuns(selectedRuns);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [docId]);

  if (loading) return <div className="p-8 text-center">Loading comparison...</div>;
  if (runIds.length === 0) return <div className="p-8 text-center text-red-500">No runs selected for comparison.</div>;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center shrink-0 py-2 px-4 border-b border-gray-200 bg-white">
        <Link to={`/documents/${docId}`} className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors shrink-0 mr-4">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Link>
        <div className="flex-1 text-center text-sm">
          <span className="text-gray-400 mx-2">←</span>
          <span className="font-semibold text-red-600">Left</span>
          <span className="text-gray-400 mx-1">:</span>
          <span className="font-semibold text-gray-700">{providers.find(p => p.provider_id === runs[0]?.provider_id)?.display_name || runs[0]?.provider_id}</span>
          {runs.length > 1 && (<>
            <span className="text-gray-300 mx-3">|</span>
            <span className="font-semibold text-blue-600">Right</span>
            <span className="text-gray-400 mx-1">:</span>
            <span className="font-semibold text-gray-700">{providers.find(p => p.provider_id === runs[1]?.provider_id)?.display_name || runs[1]?.provider_id}</span>
            <span className="text-gray-400 mx-2">→</span>
          </>)}
        </div>
        <span className="text-xs text-gray-400 shrink-0">{docName}</span>
      </div>

      <div className="flex-1 min-h-0 flex gap-4 overflow-hidden p-2">
        {runs.map((run) => (
          <div key={run.id} className="flex-1 h-full overflow-hidden">
            <PdfViewer
              src={`/api/documents/${docId}/download?v=${run.id}`}
              runId={run.id}
              sharedPlugins={sharedPluginsRef.current}
              scrollFraction={syncedScroll}
              onScrollChange={setSyncedScroll}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
