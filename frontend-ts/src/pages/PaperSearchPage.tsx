import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';
import type { SearchPaper } from '../types/api';
import { Search, Loader, ExternalLink, FileSearch, AlertCircle, BookOpen, FolderPlus, Check } from 'lucide-react';

const SOURCE_ICON: Record<string, string> = {
    arxiv: '🔬',
    pubmed: '🏥',
    ieee: '⚡',
    acm: '📖',
};

export default function PaperSearchPage() {
    const { activeWorkspace } = useAuth();
    const [searchParams] = useSearchParams();
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [papers, setPapers] = useState<SearchPaper[]>([]);
    const [error, setError] = useState('');
    const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
    const [agentLoading, setAgentLoading] = useState<string | null>(null);
    const [agentResult, setAgentResult] = useState<Record<string, unknown> | null>(null);
    const [importedPapers, setImportedPapers] = useState<Set<number>>(new Set());
    const [importingIdx, setImportingIdx] = useState<number | null>(null);
    const initialSearchDone = useRef(false);

    // Read query param from URL (from navbar search)
    useEffect(() => {
        const q = searchParams.get('q');
        if (q && !initialSearchDone.current) {
            initialSearchDone.current = true;
            setQuery(q);
            doSearch(q);
        }
    }, [searchParams]);

    const doSearch = async (q: string) => {
        if (!q.trim()) return;
        setLoading(true);
        setError('');
        setPapers([]);
        setAgentResult(null);
        setImportedPapers(new Set());
        try {
            const res = await api.searchPapers(q, 10);
            setPapers(res.papers ?? []);
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr?.response?.data?.detail || 'Search failed');
        }
        setLoading(false);
    };

    const handleSearch = async () => {
        if (!query.trim() || loading) return;
        await doSearch(query);
    };

    const handleImport = async (paper: SearchPaper, idx: number) => {
        if (!activeWorkspace) {
            setError('Select a workspace first to import papers');
            return;
        }
        setImportingIdx(idx);
        try {
            await api.importPaper(activeWorkspace.id, paper);
            setImportedPapers((prev) => new Set(prev).add(idx));
        } catch {
            setError(`Failed to import "${paper.title}"`);
        }
        setImportingIdx(null);
    };

    const runGapAnalysis = async () => {
        if (!query.trim()) return;
        setAgentLoading('gap');
        setAgentResult(null);
        try {
            const res = await api.agentGaps(query);
            setAgentResult(res.result);
        } catch { /* ignore */ }
        setAgentLoading(null);
    };

    const runSimilarPapers = async () => {
        if (!query.trim()) return;
        setAgentLoading('similar');
        setAgentResult(null);
        try {
            const res = await api.agentCompare(query);
            setAgentResult(res.result);
        } catch { /* ignore */ }
        setAgentLoading(null);
    };

    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <FileSearch size={20} style={{ color: 'var(--accent)' }} />
                Paper Search
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 16 }}>
                Search arXiv & PubMed for research papers. View abstracts, import to workspace, or run analysis.
            </p>

            {/* Search bar */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <div style={{ flex: 1, position: 'relative' }}>
                    <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        className="input"
                        style={{ paddingLeft: 36, width: '100%' }}
                        placeholder="e.g., attention mechanism in transformers"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        disabled={loading}
                    />
                </div>
                <button className="btn btn-primary" onClick={handleSearch} disabled={loading || !query.trim()}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px' }}>
                    {loading ? <Loader size={16} className="spinner-icon" /> : <Search size={16} />}
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>

            {/* Action buttons */}
            {papers.length > 0 && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    <button className="btn" onClick={runSimilarPapers} disabled={!!agentLoading}
                        style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px' }}>
                        {agentLoading === 'similar' ? <Loader size={12} className="spinner-icon" /> : <BookOpen size={12} />}
                        Similar Papers Analysis
                    </button>
                    <button className="btn" onClick={runGapAnalysis} disabled={!!agentLoading}
                        style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px' }}>
                        {agentLoading === 'gap' ? <Loader size={12} className="spinner-icon" /> : <AlertCircle size={12} />}
                        Gap Analysis
                    </button>
                </div>
            )}

            {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

            {loading && (
                <div className="card" style={{ padding: 30, textAlign: 'center' }}>
                    <div className="spinner" style={{ margin: '0 auto 12px' }} />
                    <p style={{ fontWeight: 600, fontSize: 14 }}>Searching arXiv & PubMed...</p>
                </div>
            )}

            {/* Agent result overlay */}
            {agentResult && (
                <div className="card" style={{ padding: 16, marginBottom: 16, border: '2px solid var(--accent)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <h4 style={{ fontSize: 14, fontWeight: 700 }}>Agent Result</h4>
                        <button onClick={() => setAgentResult(null)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)' }}>
                            Close
                        </button>
                    </div>
                    <pre style={{
                        fontSize: 12, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                        maxHeight: 300, overflow: 'auto', margin: 0,
                    }}>
                        {JSON.stringify(agentResult, null, 2)}
                    </pre>
                </div>
            )}

            {/* Results */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {papers.map((paper, i) => (
                    <div key={i} className="card" style={{ padding: 16 }}>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                            <span style={{ fontSize: 24 }}>{SOURCE_ICON[paper.source.toLowerCase()] ?? '📄'}</span>
                            <div style={{ flex: 1 }}>
                                <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, lineHeight: 1.4 }}>
                                    {paper.title}
                                </h3>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                                    {paper.authors} • {paper.year} • <span className="badge" style={{ fontSize: 9, textTransform: 'uppercase' }}>{paper.source}</span>
                                </div>

                                {/* Abstract toggle */}
                                <div
                                    style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--text-body)', cursor: 'pointer' }}
                                    onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                                >
                                    {expandedIdx === i
                                        ? paper.abstract
                                        : paper.abstract.slice(0, 200) + (paper.abstract.length > 200 ? '...' : '')
                                    }
                                </div>

                                {/* Actions row */}
                                <div style={{ display: 'flex', gap: 12, marginTop: 8, alignItems: 'center' }}>
                                    {paper.url && (
                                        <a
                                            href={paper.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            style={{
                                                display: 'inline-flex', alignItems: 'center', gap: 4,
                                                fontSize: 11, color: 'var(--accent)', fontWeight: 600,
                                                textDecoration: 'none',
                                            }}
                                        >
                                            <ExternalLink size={12} /> Open Original
                                        </a>
                                    )}

                                    {importedPapers.has(i) ? (
                                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#22c55e', fontWeight: 600 }}>
                                            <Check size={12} /> Imported
                                        </span>
                                    ) : (
                                        <button
                                            onClick={() => handleImport(paper, i)}
                                            disabled={importingIdx === i}
                                            style={{
                                                display: 'inline-flex', alignItems: 'center', gap: 4,
                                                fontSize: 11, color: 'var(--accent)', fontWeight: 600,
                                                background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                                            }}
                                        >
                                            {importingIdx === i ? <Loader size={12} className="spinner-icon" /> : <FolderPlus size={12} />}
                                            {importingIdx === i ? 'Importing...' : 'Import to Workspace'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {!loading && papers.length === 0 && !error && (
                <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    Enter a research topic to search for papers.
                </div>
            )}
        </div>
    );
}
