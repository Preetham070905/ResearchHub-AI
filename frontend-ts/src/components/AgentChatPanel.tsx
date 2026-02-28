/**
 * AgentChatPanel — Expandable panel for interacting with a single agent.
 * Input chatbox + result area + "View Raw Data" toggle.
 */
import { useState } from 'react';
import { Send, ChevronDown, ChevronUp, Code, FileText, Loader } from 'lucide-react';

interface Props {
    name: string;
    icon: string;
    description: string;
    onRun: (query: string) => Promise<Record<string, unknown>>;
}

export default function AgentChatPanel({ name, icon, description, onRun }: Props) {
    const [expanded, setExpanded] = useState(false);
    const [query, setQuery] = useState('');
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showRaw, setShowRaw] = useState(false);

    const handleRun = async () => {
        if (!query.trim() || loading) return;
        setLoading(true);
        setError('');
        setResult(null);
        try {
            const res = await onRun(query);
            setResult(res);
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr?.response?.data?.detail || 'Agent call failed');
        }
        setLoading(false);
    };

    const renderValue = (val: unknown): string => {
        if (typeof val === 'string') return val;
        if (Array.isArray(val)) return val.map((v) => typeof v === 'string' ? `• ${v}` : JSON.stringify(v)).join('\n');
        if (typeof val === 'object' && val !== null) return JSON.stringify(val, null, 2);
        return String(val);
    };

    return (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {/* Header */}
            <div
                onClick={() => setExpanded(!expanded)}
                style={{
                    padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10,
                    cursor: 'pointer', borderBottom: expanded ? '1px solid #e5e7eb' : 'none',
                }}
            >
                <span style={{ fontSize: 22 }}>{icon}</span>
                <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{description}</div>
                </div>
                {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>

            {/* Body */}
            {expanded && (
                <div style={{ padding: 16 }}>
                    {/* Input */}
                    <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                        <input
                            className="input"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleRun()}
                            placeholder={`Ask ${name}...`}
                            disabled={loading}
                            style={{ flex: 1 }}
                        />
                        <button
                            className="btn btn-primary"
                            onClick={handleRun}
                            disabled={loading || !query.trim()}
                            style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '8px 14px' }}
                        >
                            {loading ? <Loader size={14} className="spinner-icon" /> : <Send size={14} />}
                            {loading ? 'Running...' : 'Run'}
                        </button>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="error-msg" style={{ marginBottom: 10 }}>{error}</div>
                    )}

                    {/* Result */}
                    {result && (
                        <div>
                            {/* Toggle */}
                            <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                                <button
                                    className={`btn ${!showRaw ? 'btn-primary' : ''}`}
                                    onClick={() => setShowRaw(false)}
                                    style={{ fontSize: 11, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                                >
                                    <FileText size={12} /> Formatted
                                </button>
                                <button
                                    className={`btn ${showRaw ? 'btn-primary' : ''}`}
                                    onClick={() => setShowRaw(true)}
                                    style={{ fontSize: 11, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}
                                >
                                    <Code size={12} /> Raw JSON
                                </button>
                            </div>

                            {showRaw ? (
                                <pre style={{
                                    background: '#1f2937', color: '#e5e7eb', padding: 14,
                                    borderRadius: 8, fontSize: 11, maxHeight: 400, overflow: 'auto',
                                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                                }}>
                                    {JSON.stringify(result, null, 2)}
                                </pre>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {Object.entries(result).map(([key, val]) => {
                                        if (key === 'error' || key === 'raw_output') return null;
                                        return (
                                            <div key={key} style={{
                                                padding: '8px 12px', background: 'var(--bg-input)',
                                                borderRadius: 6, fontSize: 12,
                                            }}>
                                                <strong style={{ textTransform: 'capitalize' }}>
                                                    {key.replace(/_/g, ' ')}
                                                </strong>
                                                <pre style={{
                                                    margin: '4px 0 0', whiteSpace: 'pre-wrap',
                                                    fontSize: 12, lineHeight: 1.6, fontFamily: 'inherit',
                                                }}>
                                                    {renderValue(val)}
                                                </pre>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
