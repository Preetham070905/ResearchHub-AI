import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { GraphNode, GraphEdge } from '../types/api';
import KnowledgeGraphViz from '../components/KnowledgeGraphViz';
import { GitGraph, Search, Loader, X, AlertCircle } from 'lucide-react';

export default function GraphPage() {
    const { activeWorkspace } = useAuth();
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [nodes, setNodes] = useState<GraphNode[]>([]);
    const [edges, setEdges] = useState<GraphEdge[]>([]);
    const [kgResult, setKgResult] = useState<Record<string, unknown> | null>(null);
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

    const buildGraph = async () => {
        if (!query.trim() || loading) return;
        setLoading(true);
        setError('');
        setSelectedNode(null);
        try {
            const res = await api.agentKnowledgeGraph(query);
            setKgResult(res.result);
            setNodes(res.graph?.nodes ?? []);
            setEdges(res.graph?.edges ?? []);
        } catch (err: unknown) {
            const axiosErr = err as { response?: { data?: { detail?: string } } };
            setError(axiosErr?.response?.data?.detail || 'Failed to build knowledge graph');
        }
        setLoading(false);
    };

    const onNodeClick = useCallback((node: GraphNode) => {
        setSelectedNode(node);
    }, []);

    if (!activeWorkspace) {
        return (
            <div className="page-content">
                <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                    <AlertCircle size={32} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
                    <p style={{ color: 'var(--text-muted)' }}>Select a workspace from the Dashboard first.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="page-content" style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
                <h2 style={{ marginBottom: 6, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <GitGraph size={20} style={{ color: 'var(--accent)' }} />
                    Knowledge Graph
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 16 }}>
                    Build an interactive concept graph from research papers. Zoom, drag, and click nodes.
                </p>

                {/* Search */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="input"
                            style={{ paddingLeft: 36, width: '100%' }}
                            placeholder="e.g., graph neural networks for drug discovery"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && buildGraph()}
                            disabled={loading}
                        />
                    </div>
                    <button className="btn btn-primary" onClick={buildGraph} disabled={loading || !query.trim()}
                        style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px' }}>
                        {loading ? <Loader size={16} className="spinner-icon" /> : <GitGraph size={16} />}
                        {loading ? 'Building...' : 'Build Graph'}
                    </button>
                </div>

                {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

                {loading && (
                    <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                        <div className="spinner" style={{ margin: '0 auto 12px' }} />
                        <p style={{ fontWeight: 600, fontSize: 14 }}>🧠 Building knowledge graph...</p>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Searching papers, extracting concepts, finding connections...</p>
                    </div>
                )}

                {/* Graph */}
                {nodes.length > 0 && !loading && (
                    <>
                        {/* Stats */}
                        <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                            <div className="card" style={{ padding: '8px 16px', textAlign: 'center', flex: 1 }}>
                                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--accent)' }}>{nodes.length}</div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Nodes</div>
                            </div>
                            <div className="card" style={{ padding: '8px 16px', textAlign: 'center', flex: 1 }}>
                                <div style={{ fontSize: 22, fontWeight: 800, color: '#3b82f6' }}>{edges.length}</div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Edges</div>
                            </div>
                            <div className="card" style={{ padding: '8px 16px', textAlign: 'center', flex: 1 }}>
                                <div style={{ fontSize: 22, fontWeight: 800, color: '#22c55e' }}>
                                    {new Set(nodes.map(n => n.type)).size}
                                </div>
                                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Types</div>
                            </div>
                        </div>

                        <KnowledgeGraphViz
                            nodes={nodes}
                            edges={edges}
                            onNodeClick={onNodeClick}
                            width={Math.min(window.innerWidth - 380, 900)}
                            height={480}
                        />

                        {/* Insights */}
                        {kgResult && (
                            <div className="card" style={{ marginTop: 12, padding: 16 }}>
                                <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>Graph Insights</h4>
                                <p style={{ fontSize: 12, lineHeight: 1.7, margin: 0 }}>
                                    {(kgResult as Record<string, string>).graph_insights || 'No insights available.'}
                                </p>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Side Panel — Node Details */}
            {selectedNode && (
                <div style={{
                    width: 280, flexShrink: 0, borderLeft: '1px solid #e5e7eb',
                    padding: '16px 16px 16px 20px',
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <h3 style={{ fontSize: 14, fontWeight: 700 }}>Node Detail</h3>
                        <button onClick={() => setSelectedNode(null)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                            <X size={16} />
                        </button>
                    </div>

                    <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{selectedNode.label}</div>
                    <span className="badge badge-blue" style={{ fontSize: 10, marginBottom: 12, display: 'inline-block', textTransform: 'capitalize' }}>
                        {selectedNode.type}
                    </span>

                    <h4 style={{ fontSize: 12, fontWeight: 700, marginTop: 16, marginBottom: 6 }}>Connected Nodes</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {edges
                            .filter(e => {
                                const src = typeof e.source === 'string' ? e.source : e.source.id;
                                const tgt = typeof e.target === 'string' ? e.target : e.target.id;
                                return src === selectedNode.id || tgt === selectedNode.id;
                            })
                            .slice(0, 10)
                            .map((e, i) => {
                                const src = typeof e.source === 'string' ? e.source : e.source.id;
                                const tgt = typeof e.target === 'string' ? e.target : e.target.id;
                                const other = src === selectedNode.id ? tgt : src;
                                return (
                                    <div key={i} style={{ fontSize: 11, padding: '4px 8px', background: 'var(--bg-input)', borderRadius: 4 }}>
                                        <span style={{ fontWeight: 600 }}>{other}</span>
                                        <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>({e.relation.replace(/_/g, ' ')})</span>
                                    </div>
                                );
                            })}
                    </div>
                </div>
            )}
        </div>
    );
}
