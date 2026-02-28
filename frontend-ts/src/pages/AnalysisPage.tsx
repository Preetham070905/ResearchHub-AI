import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { AnalysisResult } from '../types/api';
import { Sparkles, Search, AlertCircle, Loader } from 'lucide-react';
import AllSections from '../components/AllSections';
import TimingCards from '../components/TimingCards';
import SystemStatus from '../components/SystemStatus';

const PROGRESS_STAGES = [
    '🔍 Classifying your research intent...',
    '📄 Searching arXiv & PubMed for papers...',
    '📝 Summarizing papers...',
    '⚖️ Running comparison & insight agents...',
    '🔬 Detecting research gaps...',
    '🧠 Building knowledge graph, scoring novelty, forecasting trends...',
    '📚 Generating literature review & roadmap...',
    '✨ Synthesizing final answer...',
];

export default function AnalysisPage() {
    const { activeWorkspace } = useAuth();
    const [searchParams] = useSearchParams();
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [pipelineTime, setPipelineTime] = useState(0);
    const [progressIdx, setProgressIdx] = useState(0);

    // Load a past result if URL has ?result=ID
    useEffect(() => {
        const resultId = searchParams.get('result');
        if (resultId) {
            setLoading(true);
            api.getResult(Number(resultId))
                .then((data) => {
                    setResult(data.result as unknown as AnalysisResult);
                    setLoading(false);
                })
                .catch(() => {
                    setError('Failed to load past result');
                    setLoading(false);
                });
        }
    }, [searchParams]);

    // Animate progress stages while loading
    useEffect(() => {
        if (!loading) { setProgressIdx(0); return; }
        const interval = setInterval(() => {
            setProgressIdx((i) => (i < PROGRESS_STAGES.length - 1 ? i + 1 : i));
        }, 5000); // each stage ~5s (pipeline takes 20-50s with parallel agents)
        return () => clearInterval(interval);
    }, [loading]);

    const handleAnalyze = async () => {
        if (!query.trim()) return;
        if (!activeWorkspace) {
            setError('Please select a workspace from the Dashboard first.');
            return;
        }

        setLoading(true);
        setError('');
        setResult(null);
        setProgressIdx(0);

        try {
            const res = await api.runAnalysis(query, activeWorkspace.id);
            setResult(res.result);
            setPipelineTime(res.pipeline_time_seconds);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Unknown error';
            // Try to get server error detail
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            const detail = axiosErr?.response?.data?.detail;
            setError(detail || `Analysis failed: ${msg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-content" style={{ display: 'flex', gap: 20 }}>
            {/* Main content */}
            <div style={{ flex: 1, minWidth: 0 }}>
                <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Sparkles size={20} style={{ color: 'var(--accent)' }} />
                    Research Analysis Pipeline
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 16 }}>
                    Enter a research topic to run the full multi-agent analysis pipeline.
                    {activeWorkspace && <span> Workspace: <strong>{activeWorkspace.name}</strong></span>}
                </p>

                {/* Query input */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="input"
                            style={{ paddingLeft: 36, width: '100%' }}
                            placeholder="e.g., neural architecture search in computer vision"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && !loading && handleAnalyze()}
                            disabled={loading}
                        />
                    </div>
                    <button
                        className="btn btn-primary"
                        onClick={handleAnalyze}
                        disabled={loading || !query.trim()}
                        style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 20px' }}
                    >
                        {loading ? <Loader size={16} className="spinner-icon" /> : <Sparkles size={16} />}
                        {loading ? 'Running...' : 'Analyze'}
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <div className="error-msg" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <AlertCircle size={16} /> {error}
                    </div>
                )}

                {/* Loading progress */}
                {loading && (
                    <div className="card" style={{ padding: 30, textAlign: 'center', marginBottom: 20 }}>
                        <div className="spinner" style={{ margin: '0 auto 16px' }} />
                        <p style={{ fontWeight: 600, fontSize: 15, marginBottom: 8 }}>
                            {PROGRESS_STAGES[progressIdx]}
                        </p>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            This typically takes 20–50 seconds. Agents are running in parallel...
                        </p>
                        {/* Progress bar */}
                        <div style={{
                            marginTop: 16, height: 4, borderRadius: 2,
                            background: '#e5e7eb', overflow: 'hidden',
                        }}>
                            <div style={{
                                height: '100%', borderRadius: 2,
                                background: 'var(--accent)',
                                width: `${((progressIdx + 1) / PROGRESS_STAGES.length) * 100}%`,
                                transition: 'width 1s ease',
                            }} />
                        </div>
                    </div>
                )}

                {/* Timing cards */}
                {result && pipelineTime > 0 && (
                    <TimingCards timing={
                        (result as unknown as { explainability_log?: { timing_breakdown?: Record<string, number> } })
                            ?.explainability_log?.timing_breakdown ?? {}
                    } total={pipelineTime} />
                )}

                {/* Results */}
                {result && <AllSections result={result} />}
            </div>

            {/* Right sidebar */}
            <div style={{ width: 240, flexShrink: 0 }}>
                <SystemStatus />
            </div>
        </div>
    );
}
