import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { PaperItem } from '../types/api';
import {
    ShieldCheck, Upload, FileText, AlertTriangle,
    CheckCircle, XCircle, ChevronDown, ChevronUp, Loader2,
    ArrowLeftRight, Type, AlertCircle, Brain, BarChart3
} from 'lucide-react';

/* ── Types ─────────────────────────────────────────── */

interface SentenceMatch {
    source_text: string;
    matched_text: string;
    similarity: number;
    matched_doc_id?: string;
}

interface PairResult {
    doc_id: string;
    doc_title: string;
    similarity_pct: number;
    matching_passages: SentenceMatch[];
}

interface LlmAnalysis {
    interpretation?: string;
    severity?: string;
    is_likely_plagiarism?: boolean;
    key_concerns?: string[];
    mitigating_factors?: string[];
    recommendations?: string[];
    common_phrasing_ratio?: number;
}

interface PlagiarismResult {
    target_doc_id: string;
    target_doc_title: string;
    overall_plagiarism_score: number;
    risk_level: string;
    summary: string;
    pair_results: PairResult[];
    top_matching_sentences: SentenceMatch[];
    stats: Record<string, unknown>;
    llm_analysis?: LlmAnalysis;
}

/* ── Utility ───────────────────────────────────────── */

function riskBadgeClass(risk: string) {
    switch (risk) {
        case 'critical': return 'badge badge-red';
        case 'high': return 'badge badge-red';
        case 'moderate': return 'badge badge-amber';
        case 'low': return 'badge badge-green';
        default: return 'badge badge-blue';
    }
}

function riskColor(risk: string) {
    switch (risk) {
        case 'critical': return 'var(--red)';
        case 'high': return '#f97316';
        case 'moderate': return 'var(--amber)';
        case 'low': return 'var(--green)';
        default: return 'var(--text-muted)';
    }
}

function riskIcon(risk: string) {
    switch (risk) {
        case 'critical':
        case 'high':
            return <XCircle size={18} style={{ color: riskColor(risk) }} />;
        case 'moderate':
            return <AlertTriangle size={18} style={{ color: riskColor(risk) }} />;
        default:
            return <CheckCircle size={18} style={{ color: riskColor(risk) }} />;
    }
}

/* ── Main Component ────────────────────────────────── */

type CheckMode = 'upload' | 'text' | 'compare';

export default function PlagiarismPage() {
    const { activeWorkspace } = useAuth();
    const workspaceId = activeWorkspace?.id ?? null;
    const [mode, setMode] = useState<CheckMode>('upload');
    const [file, setFile] = useState<File | null>(null);
    const [text, setText] = useState('');
    const [title, setTitle] = useState('');
    const [papers, setPapers] = useState<PaperItem[]>([]);
    const [paperAId, setPaperAId] = useState<number | null>(null);
    const [paperBId, setPaperBId] = useState<number | null>(null);
    const [useLlm, setUseLlm] = useState(true);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PlagiarismResult | null>(null);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!workspaceId) return;
        api.listPapers(workspaceId).then(setPapers).catch(() => { });
    }, [workspaceId]);

    const handleCheck = useCallback(async () => {
        if (!workspaceId) {
            setError('Select a workspace first.');
            return;
        }
        setError('');
        setResult(null);
        setLoading(true);

        try {
            let data: { status: string; result: PlagiarismResult | null; message?: string };

            if (mode === 'upload') {
                if (!file) { setError('Select a PDF file.'); setLoading(false); return; }
                data = await api.plagiarismCheckFile(file, workspaceId!, useLlm) as { status: string; result: PlagiarismResult | null; message?: string };
            } else if (mode === 'text') {
                if (text.trim().length < 50) { setError('Enter at least 50 characters.'); setLoading(false); return; }
                data = await api.plagiarismCheckText(text, title || 'Untitled', workspaceId!, useLlm) as { status: string; result: PlagiarismResult | null; message?: string };
            } else {
                if (!paperAId || !paperBId) { setError('Select two papers to compare.'); setLoading(false); return; }
                if (paperAId === paperBId) { setError('Select two different papers.'); setLoading(false); return; }
                data = await api.plagiarismComparePapers(paperAId, paperBId, workspaceId!, useLlm) as { status: string; result: PlagiarismResult | null; message?: string };
            }

            if (data.status === 'no_references') {
                setError(data.message || 'No reference papers found in workspace.');
            } else if (data.result) {
                setResult(data.result);
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Plagiarism check failed.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, [mode, file, text, title, workspaceId, paperAId, paperBId, useLlm]);

    if (!activeWorkspace) {
        return (
            <div className="page-content">
                <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                    <AlertCircle size={32} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
                    <p style={{ color: 'var(--text-muted)' }}>
                        Select a workspace from the Dashboard first to check plagiarism.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="page-content">
            {/* Header */}
            <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <ShieldCheck size={22} style={{ color: 'var(--accent)' }} />
                Plagiarism Checker
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 20 }}>
                Detect similarities between research papers using TF-IDF vectorization &amp; cosine similarity,
                enhanced with AI-powered contextual analysis.
                {activeWorkspace && <span> Workspace: <strong style={{ color: 'var(--text-primary)' }}>{activeWorkspace.name}</strong></span>}
            </p>

            {/* Mode tabs */}
            <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid #e5e7eb' }}>
                {([
                    { key: 'upload' as CheckMode, icon: Upload, label: 'Upload PDF' },
                    { key: 'text' as CheckMode, icon: Type, label: 'Paste Text' },
                    { key: 'compare' as CheckMode, icon: ArrowLeftRight, label: 'Compare Papers' },
                ]).map(({ key, icon: Icon, label }) => (
                    <button
                        key={key}
                        onClick={() => { setMode(key); setResult(null); setError(''); }}
                        className={`tab ${mode === key ? 'active' : ''}`}
                        style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}
                    >
                        <Icon size={14} /> {label}
                    </button>
                ))}
            </div>

            {/* Input area */}
            <div className="card" style={{ padding: 24, marginBottom: 20 }}>
                {mode === 'upload' && (
                    <div>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 600, fontSize: 13, color: 'var(--text-secondary)' }}>
                            Upload PDF to check
                        </label>
                        <div
                            style={{
                                padding: 32,
                                textAlign: 'center',
                                borderStyle: 'dashed',
                                borderColor: file ? 'var(--accent)' : '#d1d5db',
                                borderWidth: 2,
                                borderRadius: 'var(--radius-sm)',
                                background: file ? 'var(--accent-light)' : 'var(--bg-input)',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                            }}
                            onClick={() => document.getElementById('plag-file-input')?.click()}
                        >
                            <input
                                id="plag-file-input"
                                type="file"
                                accept=".pdf"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                                style={{ display: 'none' }}
                            />
                            <Upload size={28} style={{ color: file ? 'var(--accent)' : 'var(--text-muted)', marginBottom: 8 }} />
                            <p style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: 'var(--text-primary)' }}>
                                {file ? file.name : 'Click to select a PDF file'}
                            </p>
                            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                Supports .pdf files up to 50 MB
                            </p>
                        </div>
                        {file && (
                            <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <FileText size={14} style={{ color: 'var(--accent)' }} />
                                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--accent)' }}>{file.name}</span>
                                <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>
                                    {(file.size / 1024).toFixed(0)} KB
                                </span>
                            </div>
                        )}
                    </div>
                )}

                {mode === 'text' && (
                    <div>
                        <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: 'var(--text-secondary)' }}>
                            Document Title (optional)
                        </label>
                        <input
                            className="input"
                            type="text"
                            placeholder="e.g., My Research Paper"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            style={{ width: '100%', marginBottom: 14 }}
                        />
                        <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: 'var(--text-secondary)' }}>
                            Research Text
                        </label>
                        <textarea
                            className="input"
                            placeholder="Paste your research text here (min 50 characters)..."
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            rows={8}
                            style={{
                                width: '100%', resize: 'vertical', fontFamily: 'inherit',
                                lineHeight: 1.6,
                            }}
                        />
                        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                            {text.length} characters
                        </p>
                    </div>
                )}

                {mode === 'compare' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: 'var(--text-secondary)' }}>
                                Paper A (target)
                            </label>
                            <select
                                className="input"
                                value={paperAId ?? ''}
                                onChange={(e) => setPaperAId(Number(e.target.value) || null)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Select paper...</option>
                                {papers.map((p) => (
                                    <option key={p.id} value={p.id}>{p.filename}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: 'var(--text-secondary)' }}>
                                Paper B (reference)
                            </label>
                            <select
                                className="input"
                                value={paperBId ?? ''}
                                onChange={(e) => setPaperBId(Number(e.target.value) || null)}
                                style={{ width: '100%' }}
                            >
                                <option value="">Select paper...</option>
                                {papers.map((p) => (
                                    <option key={p.id} value={p.id}>{p.filename}</option>
                                ))}
                            </select>
                        </div>
                        {papers.length === 0 && (
                            <p style={{ gridColumn: 'span 2', color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: 8 }}>
                                No papers in this workspace. Upload PDFs from the Papers page first.
                            </p>
                        )}
                    </div>
                )}

                {/* LLM toggle + submit */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 20, paddingTop: 16, borderTop: '1px solid #f3f4f6' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
                        <input
                            type="checkbox"
                            checked={useLlm}
                            onChange={(e) => setUseLlm(e.target.checked)}
                            style={{ accentColor: 'var(--accent)' }}
                        />
                        <Brain size={14} />
                        AI-powered interpretation
                    </label>
                    <button
                        className="btn btn-primary"
                        onClick={handleCheck}
                        disabled={loading}
                        style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 20px' }}
                    >
                        {loading ? <Loader2 size={16} className="spinner-icon" /> : <ShieldCheck size={16} />}
                        {loading ? 'Analyzing...' : 'Check Plagiarism'}
                    </button>
                </div>
            </div>

            {/* Loading */}
            {loading && (
                <div className="card" style={{ padding: 40, textAlign: 'center', marginBottom: 20 }}>
                    <div className="spinner" style={{ margin: '0 auto 16px' }} />
                    <p style={{ fontWeight: 600, fontSize: 15, marginBottom: 6 }}>
                        Analyzing document for similarities...
                    </p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        Comparing against workspace papers using TF-IDF vectorization
                    </p>
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="error-msg" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            {/* Results */}
            {result && <PlagiarismResults result={result} />}
        </div>
    );
}


/* ── Results Component ─────────────────────────────── */

function PlagiarismResults({ result }: { result: PlagiarismResult }) {
    const [expandedPair, setExpandedPair] = useState<string | null>(null);
    const score = result.overall_plagiarism_score;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Score card */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                {/* Colored top strip */}
                <div style={{ height: 4, background: riskColor(result.risk_level) }} />

                <div style={{ padding: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 24 }}>
                        <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                                {riskIcon(result.risk_level)}
                                <span className={riskBadgeClass(result.risk_level)} style={{ textTransform: 'uppercase' }}>
                                    {result.risk_level} Risk
                                </span>
                            </div>
                            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
                                {result.target_doc_title}
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6 }}>
                                {result.summary}
                            </p>
                        </div>
                        <div style={{ textAlign: 'center', flexShrink: 0 }}>
                            <div style={{
                                fontSize: 48,
                                fontWeight: 800,
                                background: `linear-gradient(135deg, ${riskColor(result.risk_level)}, ${riskColor(result.risk_level)}cc)`,
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                            }}>
                                {score}%
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>Similarity</div>
                        </div>
                    </div>

                    {/* Similarity bar */}
                    <div className="score-bar" style={{ marginTop: 16, marginBottom: 16 }}>
                        <div
                            className="score-bar-fill"
                            style={{
                                width: `${Math.min(score, 100)}%`,
                                background: `linear-gradient(90deg, ${riskColor(result.risk_level)}, ${riskColor(result.risk_level)}88)`,
                            }}
                        />
                    </div>

                    {/* Stats row */}
                    <div className="timing-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                        {[
                            { label: 'Documents Compared', value: String(result.stats.reference_count ?? 0) },
                            { label: 'Sentence Matches', value: String(result.stats.total_sentence_matches ?? 0) },
                            { label: 'Max Similarity', value: `${result.stats.max_document_similarity ?? 0}%` },
                            { label: 'Avg Similarity', value: `${result.stats.avg_document_similarity ?? 0}%` },
                        ].map(({ label, value }) => (
                            <div className="timing-card" key={label}>
                                <div className="label">{label}</div>
                                <div className="value">{value}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* LLM Analysis */}
            {result.llm_analysis && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div className="card-header" style={{ cursor: 'default' }}>
                        <Brain size={16} className="icon" />
                        <h3>AI Interpretation</h3>
                        {result.llm_analysis.severity && (
                            <span className="badge badge-purple">{result.llm_analysis.severity}</span>
                        )}
                    </div>
                    <div className="card-body">
                        {result.llm_analysis.interpretation && (
                            <p style={{ lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 16 }}>
                                {result.llm_analysis.interpretation}
                            </p>
                        )}

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            {result.llm_analysis.key_concerns && result.llm_analysis.key_concerns.length > 0 && (
                                <div style={{
                                    padding: 14, borderRadius: 'var(--radius-sm)',
                                    background: 'var(--red-bg)', border: '1px solid #fecaca',
                                }}>
                                    <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--red)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <AlertTriangle size={14} /> Key Concerns
                                    </h4>
                                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#991b1b', lineHeight: 1.7 }}>
                                        {result.llm_analysis.key_concerns.map((c, i) => (
                                            <li key={i}>{c}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {result.llm_analysis.recommendations && result.llm_analysis.recommendations.length > 0 && (
                                <div style={{
                                    padding: 14, borderRadius: 'var(--radius-sm)',
                                    background: 'var(--green-bg)', border: '1px solid #bbf7d0',
                                }}>
                                    <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--green)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <CheckCircle size={14} /> Recommendations
                                    </h4>
                                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#166534', lineHeight: 1.7 }}>
                                        {result.llm_analysis.recommendations.map((r, i) => (
                                            <li key={i}>{r}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        {result.llm_analysis.mitigating_factors && result.llm_analysis.mitigating_factors.length > 0 && (
                            <div style={{
                                marginTop: 12, padding: 14, borderRadius: 'var(--radius-sm)',
                                background: 'var(--blue-bg)', border: '1px solid #bfdbfe',
                            }}>
                                <h4 style={{ fontSize: 13, fontWeight: 700, color: 'var(--blue)', marginBottom: 8 }}>
                                    Mitigating Factors
                                </h4>
                                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#1e40af', lineHeight: 1.7 }}>
                                    {result.llm_analysis.mitigating_factors.map((f, i) => (
                                        <li key={i}>{f}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Document pair breakdown */}
            {result.pair_results.length > 0 && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div className="card-header" style={{ cursor: 'default' }}>
                        <BarChart3 size={16} className="icon" />
                        <h3>Document-by-Document Comparison</h3>
                        <span className="badge badge-blue">{result.pair_results.length} documents</span>
                    </div>
                    <div style={{ padding: '8px 20px 20px' }}>
                        {result.pair_results.map((pair) => (
                            <div
                                key={pair.doc_id}
                                className="card"
                                style={{ marginTop: 10, border: '1px solid #e5e7eb' }}
                            >
                                <div
                                    style={{
                                        display: 'flex', justifyContent: 'space-between',
                                        alignItems: 'center', cursor: 'pointer',
                                        padding: '14px 16px',
                                    }}
                                    onClick={() => setExpandedPair(expandedPair === pair.doc_id ? null : pair.doc_id)}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
                                        <FileText size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                        <span style={{ fontWeight: 600, fontSize: 13 }}>{pair.doc_title}</span>
                                        <span className={pair.similarity_pct > 45 ? 'badge badge-red' : pair.similarity_pct > 25 ? 'badge badge-amber' : 'badge badge-green'}>
                                            {pair.similarity_pct}% similar
                                        </span>
                                        {pair.matching_passages.length > 0 && (
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                {pair.matching_passages.length} matching passages
                                            </span>
                                        )}
                                    </div>
                                    {expandedPair === pair.doc_id
                                        ? <ChevronUp size={16} style={{ color: 'var(--text-muted)' }} />
                                        : <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
                                    }
                                </div>

                                {/* Similarity bar */}
                                <div style={{ padding: '0 16px 14px' }}>
                                    <div className="score-bar">
                                        <div
                                            className="score-bar-fill"
                                            style={{
                                                width: `${Math.min(pair.similarity_pct, 100)}%`,
                                                background: pair.similarity_pct > 70 ? 'var(--red)'
                                                    : pair.similarity_pct > 45 ? '#f97316'
                                                        : pair.similarity_pct > 25 ? 'var(--amber)' : 'var(--green)',
                                            }}
                                        />
                                    </div>
                                </div>

                                {/* Matching passages (expanded) */}
                                {expandedPair === pair.doc_id && pair.matching_passages.length > 0 && (
                                    <div style={{ padding: '0 16px 16px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                            {pair.matching_passages.map((match, idx) => (
                                                <div
                                                    key={idx}
                                                    style={{
                                                        display: 'grid', gridTemplateColumns: '1fr 1fr',
                                                        gap: 12, padding: 14,
                                                        background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)',
                                                        borderLeft: `3px solid ${match.similarity > 80 ? 'var(--red)'
                                                            : match.similarity > 60 ? '#f97316' : 'var(--amber)'}`,
                                                    }}
                                                >
                                                    <div>
                                                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                                            Your Text
                                                        </div>
                                                        <p style={{
                                                            margin: 0, fontSize: 12, color: 'var(--text-secondary)',
                                                            lineHeight: 1.6, fontStyle: 'italic',
                                                        }}>
                                                            &ldquo;{match.source_text}&rdquo;
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                                                            Matched in: {pair.doc_title}
                                                        </div>
                                                        <p style={{
                                                            margin: 0, fontSize: 12, color: 'var(--text-secondary)',
                                                            lineHeight: 1.6, fontStyle: 'italic',
                                                        }}>
                                                            &ldquo;{match.matched_text}&rdquo;
                                                        </p>
                                                    </div>
                                                    <div style={{
                                                        gridColumn: 'span 2', textAlign: 'right',
                                                    }}>
                                                        <span className={match.similarity > 80 ? 'badge badge-red' : 'badge badge-amber'}>
                                                            {match.similarity}% match
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
