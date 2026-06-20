import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiClient } from '../apiClient';
import { SourceDocumentDTO, AnalysisRunDTO, ProviderDefinition } from '../types';
import { ArrowLeft, Play, Download, Clock, AlertCircle, CheckCircle, Loader2, File, Info, History, X } from 'lucide-react';
import { format } from 'date-fns';
import { PdfViewer } from '../components/PdfViewer';

export function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<SourceDocumentDTO | null>(null);
  const [runs, setRuns] = useState<AnalysisRunDTO[]>([]);
  const [providers, setProviders] = useState<ProviderDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showRunModal, setShowRunModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [triggeringRun, setTriggeringRun] = useState(false);
  
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const loadDocumentData = async () => {
    try {
      const [docRes, runsRes, provRes] = await Promise.all([
        apiClient.get<SourceDocumentDTO>(`/documents/${id}`),
        apiClient.get<AnalysisRunDTO[]>(`/documents/${id}/analysis-runs`),
        apiClient.get<ProviderDefinition[]>('/providers')
      ]);
      setDoc(docRes.data);
      setRuns(runsRes.data);
      setProviders(provRes.data);
      if (provRes.data.length > 0) setSelectedProvider(provRes.data[0].provider_id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadRef = useRef(loadDocumentData);
  loadRef.current = loadDocumentData;

  useEffect(() => {
    loadDocumentData();
  }, [id]);

  // Long-poll active runs for this document
  useEffect(() => {
    const activeRuns = runs.filter(r => r.status === 'pending' || r.status === 'queued' || r.status === 'running');
    if (activeRuns.length === 0) return;

    let stopped = false;
    const runIds = activeRuns.map(r => r.id);

    const poll = async () => {
      while (!stopped) {
        try {
          const results = await Promise.all(
            runIds.map(runId =>
              apiClient.get(`/analysis-runs/${runId}/poll?timeout=25`).catch(() => null)
            )
          );
          const changed = results.some(r => r?.data?.changed);
          if (changed && !stopped) {
            await loadRef.current();
            return;
          }
        } catch {
          // ignore errors, retry after delay
        }
        if (!stopped) {
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
      }
    };
    poll();

    return () => { stopped = true; };
  }, [runs, id]);

  const handleTriggerRun = async () => {
    setTriggeringRun(true);
    try {
      await apiClient.post(`/documents/${id}/analysis-runs`, {
        provider_id: selectedProvider,
        config: {}
      });
      setShowRunModal(false);
      loadDocumentData();
    } catch (e) {
      console.error(e);
    } finally {
      setTriggeringRun(false);
    }
  };

  const toggleRunSelection = (runId: string) => {
    const next = new Set(selectedRuns);
    if (next.has(runId)) next.delete(runId);
    else next.add(runId);
    setSelectedRuns(next);
  };

  const closeHistoryModal = () => {
    setShowHistoryModal(false);
    setSelectedRuns(new Set());
  };

  const handleCompare = () => {
    if (selectedRuns.size < 2) return;
    navigate(`/documents/${id}/compare?runs=${Array.from(selectedRuns).join(',')}`);
  };

  const successfulRuns = runs.filter(r => r.status === 'success');
  const activeRun = successfulRuns.find(r => r.id === activeRunId);

  if (loading && !doc) return <div className="p-8 text-center">Loading...</div>;
  if (!doc) return <div className="p-8 text-center text-red-500">Document not found</div>;

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Secondary Navigation */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0 shadow-sm z-10">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/documents')} 
            className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors group"
            title="Back to Documents"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
          </button>
          <div className="min-w-0">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight truncate max-w-[16rem] sm:max-w-[22rem] md:max-w-[30rem]" title={doc.name}>
              {doc.name}
            </h2>
            <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500 font-medium">
              <span className="text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded uppercase">{doc.mime_type.split('/')[1]}</span>
              <span>{(doc.size_bytes / 1024).toFixed(0)} KB</span>
              <span>•</span>
              <span>{doc.page_count} Pages</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {successfulRuns.length > 0 && (
            <div className="flex items-center gap-2 mr-2 pr-4 border-r border-gray-200 hidden sm:flex">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Show Extraction:</span>
              <select
                className="bg-gray-50 border border-gray-200 text-gray-700 py-1.5 pl-3 pr-8 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm font-semibold shadow-sm cursor-pointer"
                value={activeRunId || ''}
                onChange={(e) => setActiveRunId(e.target.value || null)}
              >
                <option value="">None (Original)</option>
                {(() => {
                  // Deduplicate providers: show one option per provider and
                  // use the latest successful run id for that provider.
                  const latestByProvider: Record<string, any> = {};
                  for (const r of successfulRuns) {
                    // choose the latest by started_at (fallback to created_at)
                    const ts = r.started_at ? new Date(r.started_at).getTime() : new Date(r.created_at || 0).getTime();
                    const prev = latestByProvider[r.provider_id];
                    if (!prev || ts > prev._ts) {
                      latestByProvider[r.provider_id] = { ...r, _ts: ts };
                    }
                  }
                  return Object.values(latestByProvider).map((run: any) => (
                    <option key={run.id} value={run.id}>
                      {providers.find(p => p.provider_id === run.provider_id)?.display_name || run.provider_id}
                    </option>
                  ));
                })()}
              </select>
            </div>
          )}

          <button
            onClick={() => setShowDetailsModal(true)}
            className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
            title="File Details"
          >
            <Info className="w-5 h-5" />
          </button>
          
          <button
            onClick={() => setShowHistoryModal(true)}
            className="inline-flex items-center px-2.5 py-1.5 border border-gray-200 shadow-sm text-xs font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-300 transition-all"
            title="Runs & Compare"
          >
            <History className="w-3.5 h-3.5 mr-1.5 text-indigo-500" />
            Runs & Compare
          </button>

          <button
            onClick={() => setShowRunModal(true)}
            className="inline-flex items-center px-2.5 py-1.5 border border-transparent shadow-sm text-xs font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 transition-all"
            title="Run Analysis"
          >
            <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
            Run Analysis
          </button>
        </div>
      </div>

      <div className="flex-1 bg-gray-100 flex overflow-hidden">
        {/* Main View: PDF Viewer */}
        <div className="flex-1 flex flex-col items-center justify-center overflow-auto relative">
          
          <div className="absolute top-4 right-6 z-10 flex gap-2">
             <button className="p-2 bg-white/80 backdrop-blur border border-gray-200 rounded-lg shadow-sm hover:border-indigo-300 hover:bg-white text-gray-600 hover:text-indigo-600 flex items-center transition-all">
               <Download className="w-4 h-4" />
             </button>
          </div>

          <div className="w-full h-full">
            <PdfViewer src={`/api/documents/${id}/download`} runId={activeRunId} />
          </div>
        </div>
      </div>

      {/* Popups */}
      {showHistoryModal && (
        <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center p-4 z-[100] backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/80">
              <h3 className="font-bold text-gray-900 flex items-center text-lg">
                <History className="w-5 h-5 mr-2 text-indigo-500" />
                Analysis Runs & Compare
              </h3>
              <button onClick={closeHistoryModal} className="p-1.5 hover:bg-gray-200 rounded-full transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5">
              {runs.length === 0 ? (
                <div className="py-16 flex flex-col items-center justify-center text-gray-400">
                  <History className="w-12 h-12 mb-4 opacity-20" />
                  <p className="text-sm font-medium">No analysis runs yet.</p>
                  <p className="text-xs mt-1">Run an analysis to see history here.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-indigo-50 border border-indigo-100 p-3 rounded-lg flex items-start gap-3">
                    <Info className="w-5 h-5 text-indigo-600 shrink-0" />
                    <p className="text-xs text-indigo-800 leading-relaxed">
                      Select two successful runs to compare their extraction differences side-by-side.
                      You can also quickly view a run's extraction directly from the top navigation bar.
                    </p>
                  </div>
                  
                  <div className="space-y-3">
                    {runs.map(run => (
                      <div key={run.id} className={`p-4 rounded-xl border transition-all flex items-center gap-4 ${activeRunId === run.id ? 'border-amber-400 bg-amber-50/50' : 'border-gray-200 hover:border-indigo-300'}`}>
                        {run.status === 'success' && (
                          <div className="shrink-0 flex items-center justify-center">
                            <input 
                              type="checkbox"
                              className="h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer transition-colors"
                              checked={selectedRuns.has(run.id)}
                              onChange={() => toggleRunSelection(run.id)}
                              disabled={!selectedRuns.has(run.id) && selectedRuns.size >= 2}
                            />
                          </div>
                        )}
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-bold text-gray-900">
                              {providers.find(p => p.provider_id === run.provider_id)?.display_name || run.provider_id}
                            </p>
                            <span className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider ${
                              run.status === 'success' ? 'bg-green-100 text-green-700' :
                              run.status === 'failed' ? 'bg-red-100 text-red-700' :
                              'bg-amber-100 text-amber-700 animate-pulse'
                            }`}>
                              {run.status}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 mt-1.5 text-xs text-gray-500 font-medium">
                             <span className="flex items-center">
                               <Clock className="w-3.5 h-3.5 mr-1" />
                               {run.started_at ? format(new Date(run.started_at), 'PPPp') : 'Pending...'}
                             </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-5 border-t border-gray-100 bg-white">
               <div className="flex justify-between items-center">
                 <div className="flex items-center gap-3">
                   <span className="text-xs text-gray-500 font-medium">{runs.length} total runs</span>
                   {selectedRuns.size > 0 && (
                     <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 text-[11px] font-bold">
                       <CheckCircle className="w-3 h-3" />
                       {selectedRuns.size}/2 selected
                     </span>
                   )}
                 </div>
                 <div className="flex gap-3">
                    <button
                      onClick={handleCompare}
                      disabled={selectedRuns.size !== 2}
                      className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      <Play className="w-4 h-4 mr-2 fill-current" />
                      Compare
                    </button>
                    <button
                      onClick={closeHistoryModal}
                      className="px-5 py-2.5 text-gray-600 text-sm font-semibold hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      Close
                    </button>
                 </div>
               </div>
            </div>
          </div>
        </div>
      )}

      {showDetailsModal && doc && (
        <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center p-4 z-[100] backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900 flex items-center text-lg">
                <Info className="w-5 h-5 mr-2 text-indigo-500" />
                Document Details
              </h3>
              <button onClick={() => setShowDetailsModal(false)} className="p-1.5 hover:bg-gray-200 rounded-full transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <dt className="text-gray-400 text-[10px] uppercase tracking-widest font-bold mb-1">Mime Type</dt>
                  <dd className="text-sm text-gray-900 font-semibold">{doc.mime_type}</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-[10px] uppercase tracking-widest font-bold mb-1">File Size</dt>
                  <dd className="text-sm text-gray-900 font-semibold">{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-[10px] uppercase tracking-widest font-bold mb-1">Pages</dt>
                  <dd className="text-sm text-gray-900 font-semibold">{doc.page_count} Pages</dd>
                </div>
                <div>
                  <dt className="text-gray-400 text-[10px] uppercase tracking-widest font-bold mb-1">ID</dt>
                  <dd className="text-xs text-gray-500 font-mono font-medium truncate" title={doc.id}>{doc.id}</dd>
                </div>
              </div>
              <div className="pt-4 border-t border-gray-100">
                <dt className="text-gray-400 text-[10px] uppercase tracking-widest font-bold mb-1">Uploaded Date</dt>
                <dd className="text-sm text-gray-900 font-semibold">{format(new Date(doc.created_at), 'PPPPpppp')}</dd>
              </div>
            </div>
          </div>
        </div>
      )}

      {showRunModal && (
        <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center p-4 z-[100] backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-gray-900 flex items-center text-lg">
                <Play className="w-5 h-5 mr-2 text-indigo-500 fill-current" />
                Run New Analysis
              </h3>
              <button onClick={() => setShowRunModal(false)} className="p-1.5 hover:bg-gray-200 rounded-full transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-700 mb-2">Analysis Provider</label>
                <select 
                  className="mt-1 block w-full pl-3 pr-10 py-2.5 text-base border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-lg border shadow-sm"
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                >
                  {providers.map(p => (
                    <option key={p.provider_id} value={p.provider_id}>{p.display_name}</option>
                  ))}
                </select>
                <p className="mt-2 text-xs text-gray-500">
                  Select the provider to run on this document.
                </p>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button 
                  onClick={() => setShowRunModal(false)}
                  className="px-5 py-2.5 text-sm font-semibold rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleTriggerRun}
                  disabled={triggeringRun}
                  className="px-6 py-2.5 text-sm font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm disabled:opacity-50 flex items-center transition-colors"
                >
                  {triggeringRun ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2 fill-current" />}
                  Start Analysis
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
