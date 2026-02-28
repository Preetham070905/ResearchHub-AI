import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { AnalysisHistoryItem } from '../types/api';
import ConfidenceGauge from '../components/ConfidenceGauge';
import { BarChart3, AlertCircle, TrendingUp, Lightbulb, Target, Beaker } from 'lucide-react';

export default function InsightsPage() {
    const { activeWorkspace } = useAuth();
    const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [data, setData] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (activeWorkspace) {
            api.getHistory(activeWorkspace.id).then(setHistory).catch(() => { });
        }
    }, [activeWorkspace]);

    const loadInsights = async (id: number) => {
        setSelectedId(id);
        setLoading(true);
        try {
            const res = await api.getResult(id);
            setData(res.result as Record<string, unknown>);
        } catch {
            setData(null);
        }
        setLoading(false);
    };

    if (!activeWorkspace) {
        return (
            <div className="page-content">
                <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                    <AlertCircle size={32} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
                    <p style={{ color: 'var(--text-muted)' }}>Select a workspace first.</p>
                </div>
            </div>
        );
    }

    const novelty = data?.novelty_score as Record<string, unknown> | undefined;
    const confidence = data?.confidence_score as Record<string, unknown> | undefined;
    const trend = data?.trend_forecast as Record<string, unknown> | undefined;
    const gaps = data?.gap_analysis as Record<string, unknown> | undefined;
    const methods = data?.recommended_methods_datasets as Record<string, unknown> | undefined;

    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 16, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <BarChart3 size={20} style={{ color: 'var(--accent)' }} />
                Research Insights
            </h2>

            {history.length === 0 ? (
                <div className="card" style={{ padding: 30, textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-muted)' }}>Run an analysis first to see insights.</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 16 }}>
                    {/* Selector */}
                    <div className="card" style={{ padding: 12 }}>
                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>Select Analysis</h4>
                        {history.map((h) => (
                            <div
                                key={h.id}
                                onClick={() => loadInsights(h.id)}
                                style={{
                                    padding: '8px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                                    background: selectedId === h.id ? 'var(--accent-light)' : 'transparent',
                                    border: selectedId === h.id ? '1px solid var(--accent)' : '1px solid transparent',
                                    marginBottom: 4, fontWeight: 500,
                                }}
                            >
                                {h.query}
                            </div>
                        ))}
                    </div>

                    {/* Content */}
                    <div>
                        {loading ? (
                            <div className="card" style={{ padding: 40, textAlign: 'center' }}><div className="spinner" /></div>
                        ) : !data ? (
                            <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Click an analysis to view insights.</p>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                {/* Score cards + Confidence Gauge */}
                                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, flex: 1 }}>
                                        <div className="card" style={{ padding: 14, textAlign: 'center' }}>
                                            <Lightbulb size={18} style={{ color: 'var(--accent)', marginBottom: 4 }} />
                                            <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--accent)' }}>
                                                {(novelty?.overall_score as number) ?? '—'}
                                            </div>
                                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Novelty</div>
                                        </div>
                                        <div className="card" style={{ padding: 14, textAlign: 'center' }}>
                                            <TrendingUp size={18} style={{ color: '#3b82f6', marginBottom: 4 }} />
                                            <div style={{ fontSize: 26, fontWeight: 800, color: '#3b82f6' }}>
                                                {Array.isArray((trend as Record<string, unknown>)?.emerging_topics)
                                                    ? (trend as Record<string, string[]>).emerging_topics.length : '—'}
                                            </div>
                                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Trends</div>
                                        </div>
                                        <div className="card" style={{ padding: 14, textAlign: 'center' }}>
                                            <Target size={18} style={{ color: '#22c55e', marginBottom: 4 }} />
                                            <div style={{ fontSize: 26, fontWeight: 800, color: '#22c55e' }}>
                                                {Array.isArray((gaps as Record<string, unknown>)?.novel_research_directions)
                                                    ? (gaps as Record<string, string[]>).novel_research_directions.length : '—'}
                                            </div>
                                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Gaps Found</div>
                                        </div>
                                    </div>

                                    {/* Confidence Gauge */}
                                    <div className="card" style={{ padding: 16, display: 'flex', justifyContent: 'center' }}>
                                        <ConfidenceGauge
                                            score={(confidence?.overall as number) ?? 0}
                                            size={100}
                                        />
                                    </div>
                                </div>

                                {/* Recommendations */}
                                {methods && !('error' in methods) && (
                                    <div className="card" style={{ padding: 16 }}>
                                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <Beaker size={14} /> Recommended Methods & Datasets
                                        </h4>
                                        {Object.entries(methods).map(([key, val]) => (
                                            <div key={key} style={{ marginBottom: 8 }}>
                                                <strong style={{ fontSize: 12, textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</strong>
                                                <div style={{ fontSize: 12, marginTop: 2 }}>
                                                    {Array.isArray(val)
                                                        ? (val as string[]).map((v, i) => (
                                                            <span key={i} className="badge" style={{ margin: '2px 4px 2px 0', fontSize: 10 }}>
                                                                {typeof v === 'string' ? v : JSON.stringify(v)}
                                                            </span>
                                                        ))
                                                        : <span>{String(val)}</span>
                                                    }
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Novelty explanation */}
                                {novelty?.explanation && (
                                    <div className="card" style={{ padding: 16 }}>
                                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>Novelty Analysis</h4>
                                        <p style={{ fontSize: 12, lineHeight: 1.7, margin: 0 }}>{novelty.explanation as string}</p>
                                    </div>
                                )}

                                {/* Gap Analysis */}
                                {gaps && !('error' in gaps) && Array.isArray(gaps.novel_research_directions) && (
                                    <div className="card" style={{ padding: 16 }}>
                                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>Research Gaps</h4>
                                        <ul style={{ fontSize: 12, lineHeight: 1.8, margin: 0, paddingLeft: 16 }}>
                                            {(gaps.novel_research_directions as string[]).slice(0, 5).map((g, i) => (
                                                <li key={i}>{typeof g === 'string' ? g : JSON.stringify(g)}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Confidence breakdown */}
                                {confidence?.factors && (
                                    <div className="card" style={{ padding: 16 }}>
                                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>Confidence Breakdown</h4>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                            {Object.entries(confidence.factors as Record<string, number>).map(([factor, val]) => (
                                                <div key={factor} style={{
                                                    display: 'flex', alignItems: 'center', gap: 8,
                                                    padding: '6px 10px', fontSize: 12, borderRadius: 6, background: 'var(--bg-input)',
                                                }}>
                                                    <span style={{ flex: 1, textTransform: 'capitalize' }}>{factor.replace(/_/g, ' ')}</span>
                                                    <span style={{ fontWeight: 700, color: val > 0.7 ? '#22c55e' : val > 0.4 ? '#f59e0b' : '#ef4444' }}>
                                                        {(val * 100).toFixed(0)}%
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
