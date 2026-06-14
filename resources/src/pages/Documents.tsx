import { useState, useEffect, ChangeEvent, MouseEvent, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Upload, File, Search, Play, Loader2, Eye, Trash2, X, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { apiClient } from '../apiClient';
import { SourceDocumentDTO, SourceDocumentListDTO, ProviderDefinition, LatestRunSummary, DocumentRunsDTO } from '../types';
import { format } from 'date-fns';

export function Documents() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<SourceDocumentDTO[]>([]);
  const [documentRuns, setDocumentRuns] = useState<DocumentRunsDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadTotal, setUploadTotal] = useState(0);
  const [uploadDone, setUploadDone] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [documentToAnalyze, setDocumentToAnalyze] = useState<string | null>(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [providers, setProviders] = useState<ProviderDefinition[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [triggeringRun, setTriggeringRun] = useState(false);
  const [viewingDoc, setViewingDoc] = useState<SourceDocumentDTO | null>(null);

  const loadDocuments = async () => {
    try {
      const res = await apiClient.get<SourceDocumentListDTO>('/documents');
      setDocs(res.data.items);
      setDocumentRuns(res.data.document_runs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadRef = useRef(loadDocuments);
  loadRef.current = loadDocuments;

  useEffect(() => {
    loadDocuments();
    apiClient.get<ProviderDefinition[]>('/providers').then(res => {
      setProviders(res.data);
      if (res.data.length > 0) setSelectedProvider(res.data[0].provider_id);
    }).catch(console.error);
  }, []);

  // Long-poll active runs
  useEffect(() => {
    const activeRuns = documentRuns
      .flatMap(dr => dr.runs)
      .filter(r => r.status === 'pending' || r.status === 'queued' || r.status === 'running');

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
  }, [documentRuns]);

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setUploading(true);
    setUploadTotal(files.length);
    setUploadDone(0);
    let done = 0;
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        await apiClient.post('/documents', formData);
      } catch (err) {
        console.error('Failed to upload', file.name, err);
      }
      done += 1;
      setUploadDone(done);
    }
    setUploading(false);
    setUploadTotal(0);
    setUploadDone(0);
    loadDocuments();
    if (e.target) e.target.value = '';
  };

  const handleDelete = async (docId: string, e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await apiClient.delete(`/documents/${docId}`);
      loadDocuments();
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerRun = async () => {
    if (!documentToAnalyze) return;
    setTriggeringRun(true);
    try {
      await apiClient.post(`/documents/${documentToAnalyze}/analysis-runs`, {
        provider_id: selectedProvider,
        config: {}
      });
      setShowRunModal(false);
      setDocumentToAnalyze(null);
      loadDocuments();
    } catch (e) {
      console.error(e);
    } finally {
      setTriggeringRun(false);
    }
  };

  const filteredDocs = docs.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusBadge = (run: LatestRunSummary, displayName: string) => {
    const base = "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide";
    switch (run.status) {
      case 'success':
        return <span className={`${base} bg-green-100 text-green-700`}><CheckCircle className="w-3 h-3" />{displayName}</span>;
      case 'failed':
        return <span className={`${base} bg-red-100 text-red-700`}><AlertCircle className="w-3 h-3" />{displayName}</span>;
      case 'running':
        return <span className={`${base} bg-blue-100 text-blue-700 animate-pulse`}><Loader2 className="w-3 h-3 animate-spin" />{displayName}</span>;
      case 'queued':
      case 'pending':
        return <span className={`${base} bg-amber-100 text-amber-700`}><Clock className="w-3 h-3" />{displayName}</span>;
      default:
        return <span className={`${base} bg-gray-100 text-gray-600`}>{displayName}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Document Management</h2>
          <p className="text-sm text-gray-500">Upload and manage source documents for analysis.</p>
        </div>
        <div className="relative">
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept="application/pdf"
            multiple
            onChange={handleUpload}
            disabled={uploading}
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer inline-flex items-center px-4 py-2 bg-indigo-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none disabled:opacity-50"
          >
            <Upload className="w-4 h-4 mr-2" />
            {uploading ? `Uploading ${uploadDone}/${uploadTotal}...` : 'Upload PDFs'}
          </label>
        </div>
      </div>

      <div className="bg-white shadow-sm border border-gray-200 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search documents..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 sm:text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading documents...</div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-16 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-indigo-50 text-indigo-500 rounded-2xl flex items-center justify-center mb-4 border border-indigo-100">
               <Upload className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              {searchQuery ? "No matching documents" : "Upload your first document"}
            </h3>
            <p className="text-gray-500 text-sm max-w-sm mb-6">
              {searchQuery 
                ? `We couldn't find any documents matching "${searchQuery}"` 
                : "Get started by uploading a PDF document. You'll be able to run distinct extraction algorithms and compare their results."
              }
            </p>
            {!searchQuery && (
              <div className="relative">
                <input
                  type="file"
                  id="empty-file-upload"
                  className="hidden"
                  accept="application/pdf"
                  multiple
                  onChange={handleUpload}
                  disabled={uploading}
                />
                <label
                  htmlFor="empty-file-upload"
                  className="cursor-pointer inline-flex items-center px-5 py-2.5 bg-indigo-600 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white hover:bg-indigo-700 focus:outline-none disabled:opacity-50 transition-colors"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {uploading ? `Uploading ${uploadDone}/${uploadTotal}...` : 'Select PDF Files'}
                </label>
              </div>
            )}
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredDocs.map(doc => (
              <li key={doc.id}>
                <div className="hover:bg-gray-50 transition-colors">
                  <div className="px-4 py-4 sm:px-6 flex items-center justify-between">
                    <div className="flex items-center min-w-0 gap-4 flex-1">
                      <div className="p-2 bg-gray-100 rounded-lg text-gray-500 shrink-0">
                        <File className="w-6 h-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link to={`/documents/${doc.id}`} className="text-sm font-medium text-indigo-600 hover:text-indigo-800 truncate block">
                          {doc.name}
                        </Link>
                        <p className="text-xs text-gray-500 mt-1 flex gap-2">
                          <span>{doc.page_count} pages</span>
                          <span>&bull;</span>
                          <span>{(doc.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                          <span>&bull;</span>
                          <span>{format(new Date(doc.created_at), 'PPP')}</span>
                        </p>
                        {documentRuns.find(dr => dr.document_id === doc.id)?.runs && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {documentRuns.find(dr => dr.document_id === doc.id)!.runs.map(run => {
                              const provider = providers.find(p => p.provider_id === run.provider_id);
                              return <span key={run.provider_id}>{statusBadge(run, provider?.display_name || run.provider_id)}</span>;
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                      <div className="flex items-center gap-3">
                        <Link
                          to={`/documents/${doc.id}`}
                          target="_blank"
                          className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md flex items-center transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" />
                          View
                        </Link>
                        <button
                          onClick={() => { setDocumentToAnalyze(doc.id); setShowRunModal(true); }}
                          className="px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-md flex items-center transition-colors"
                        >
                          <Play className="w-3.5 h-3.5 mr-1" />
                          Analyze
                        </button>
                        <button
                          onClick={(e) => handleDelete(doc.id, e)}
                          className="p-1.5 rounded-md text-red-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="Delete document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {showRunModal && (
        <div className="fixed inset-0 bg-gray-900/60 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
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
