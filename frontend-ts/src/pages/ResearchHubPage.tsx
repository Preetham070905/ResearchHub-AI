/**
 * ResearchHubPage — Combined RAG + Agents workflow.
 * User enters query → Papers searched → Agents process → Structured output.
 */
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import ConfidenceGauge from '../components/ConfidenceGauge';
import AllSections from '../components/AllSections';
import type { AnalysisResult } from '../types/api';
import { Sparkles, Search, Loader, AlertCircle, Zap } from 'lucide-react';

const PIPELINE_STEPS = [
    { label: 'Classifying intent', icon: '🎯', key: 'intent' },
    { label: 'Searching papers (arXiv + PubMed)', icon: '📄', key: 'search' },
    { label: 'Summarizing papers', icon: '📝', key: 'summarize' },
    { label: 'Comparing methodologies', icon: '⚖️', key: 'compare' },
    { label: 'Extracting insights', icon: '💡', key: 'insight' },
    { label: 'Detecting gaps', icon: '🔍', key: 'gaps' },
    { label: 'Building knowledge graph', icon: '🕸️', key: 'kg' },
    { label: 'Scoring novelty', icon: '🆕', key: 'novelty' },
    { label: 'Forecasting trends', icon: '📈', key: 'trend' },
    { label: 'Evaluating arguments', icon: '🧐', key: 'critique' },
    { label: 'Creating roadmap', icon: '🗺️', key: 'roadmap' },
    { label: 'Writing literature review', icon: '📚', key: 'lit' },
    { label: 'Synthesizing final answer', icon: '✨', key: 'final' },
];

export default function ResearchHubPage() {
    const { activeWorkspace } = useAuth();
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [pipelineTime, setPipelineTime] = useState(0);
    const [stepIdx, setStepIdx] = useState(0);

    const handleRun = async () => {
        if (!query.trim() || loading) return;
        if (!activeWorkspace) {
            setError('Select a workspace from the Dashboard first.');
            return;
        }
        setLoading(true);
        setError('');
        setResult(null);
        setStepIdx(0);

        // Animate pipeline steps
        const timer = setInterval(() => {
            setStepIdx(i => Math.min(i + 1, PIPELINE_STEPS.length - 1));
        }, 6000);

        try {
            const res = await api.runAnalysis(query, activeWorkspace.id);
            setResult(res.result);
            setPipelineTime(res.pipeline_time_seconds);
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr?.response?.data?.detail || 'Pipeline failed');
        }
        clearInterval(timer);
        setLoading(false);
    };

    const confidence = result?.confidence_score?.overall ?? 0;

    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Zap size={20} style={{ color: 'var(--accent)' }} />
                Research Hub — Full Pipeline
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 16 }}>
                Enter a research topic. All 11 agents will process it end-to-end and produce a structured 16-section report.
                {activeWorkspace && <span> Workspace: <strong>{activeWorkspace.name}</strong></span>}
            </p>

            {/* Query */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
                <div style={{ flex: 1, position: 'relative' }}>
                    <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        className="input"
                        style={{ paddingLeft: 36, width: '100%' }}
                        placeholder="e.g., federated learning privacy mechanisms"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !loading && handleRun()}
                        disabled={loading}
                    />
                </div>
                <button className="btn btn-primary" onClick={handleRun} disabled={loading || !query.trim()}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 20px' }}>
                    {loading ? <Loader size={16} className="spinner-icon" /> : <Sparkles size={16} />}
                    {loading ? 'Running...' : 'Run Full Pipeline'}
                </button>
            </div>

            {error && <div className="error-msg" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertCircle size={16} /> {error}
            </div>}

            {/* Pipeline progress */}
            {loading && (
                <div className="card" style={{ padding: 20, marginBottom: 20 }}>
                    <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Pipeline Progress</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {PIPELINE_STEPS.map((step, i) => (
                            <div key={step.key} style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                padding: '6px 10px', borderRadius: 6, fontSize: 12,
                                background: i === stepIdx ? 'var(--accent-light)' : i < stepIdx ? '#f0fdf4' : 'transparent',
                                fontWeight: i === stepIdx ? 700 : 400,
                                opacity: i > stepIdx ? 0.4 : 1,
                                transition: 'all 0.3s ease',
                            }}>
                                <span style={{ fontSize: 16 }}>{step.icon}</span>
                                <span>{step.label}</span>
                                {i < stepIdx && <span style={{ marginLeft: 'auto', color: '#22c55e' }}>✓</span>}
                                {i === stepIdx && <Loader size={12} className="spinner-icon" style={{ marginLeft: 'auto' }} />}
                            </div>
                        ))}
                    </div>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
                        All 11 agents working in parallel... (~30-90 seconds)
                    </p>
                </div>
            )}

            {/* Results */}
            {result && (
                <>
                    {/* Confidence + timing */}
                    <div style={{ display: 'flex', gap: 16, marginBottom: 20, alignItems: 'center' }}>
                        <ConfidenceGauge score={confidence} />
                        <div>
                            <div style={{ fontSize: 13, fontWeight: 700 }}>Pipeline Complete</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                Completed in {pipelineTime.toFixed(1)}s
                            </div>
                            {result.explainability_log && (
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                    {result.explainability_log.agents_activated?.length ?? 0} / {result.explainability_log.total_agents ?? 11} agents activated
                                </div>
                            )}
                        </div>
                    </div>

                    <AllSections result={result} />
                </>
            )}
        </div>
    );
}
