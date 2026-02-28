import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { AnalysisHistoryItem } from '../types/api';
import {
    FolderOpen, Plus, Trash2, Upload, Sparkles,
    Clock, ArrowRight, CheckCircle2
} from 'lucide-react';

export default function DashboardPage() {
    const {
        workspaces, activeWorkspace, createWorkspace,
        deleteWorkspace, setActiveWorkspace
    } = useAuth();
    const navigate = useNavigate();
    const [newName, setNewName] = useState('');
    const [creating, setCreating] = useState(false);
    const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
    const [confirmDeleteWs, setConfirmDeleteWs] = useState<number | null>(null);

    useEffect(() => {
        if (activeWorkspace) {
            api.getHistory(activeWorkspace.id).then(setHistory).catch(() => setHistory([]));
        } else {
            setHistory([]);
        }
    }, [activeWorkspace]);

    const handleCreate = async () => {
        if (!newName.trim() || creating) return;
        setCreating(true);
        try {
            await createWorkspace(newName.trim());
            setNewName('');
        } catch { /* ignore */ }
        setCreating(false);
    };

    // Determine workflow step
    const step = !workspaces.length ? 1 : !activeWorkspace ? 2 : 3;

    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 6, fontSize: 22, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <FolderOpen size={22} style={{ color: 'var(--accent)' }} />
                Dashboard
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 24 }}>
                Follow the steps below to start your research analysis.
            </p>

            {/* ── Workflow Steps ── */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 28 }}>
                {[
                    { n: 1, label: 'Create Workspace', done: workspaces.length > 0 },
                    { n: 2, label: 'Upload PDFs', done: false },
                    { n: 3, label: 'Run Analysis', done: history.length > 0 },
                ].map((s) => (
                    <div
                        key={s.n}
                        style={{
                            flex: 1, padding: '14px 16px', borderRadius: 10,
                            background: step === s.n ? 'var(--accent)' : s.done ? '#e8f5e9' : 'var(--bg-card)',
                            color: step === s.n ? '#fff' : s.done ? '#2e7d32' : 'var(--text-body)',
                            display: 'flex', alignItems: 'center', gap: 8,
                            fontWeight: 600, fontSize: 13, border: '1px solid transparent',
                            borderColor: step === s.n ? 'var(--accent)' : '#e5e7eb',
                        }}
                    >
                        {s.done ? <CheckCircle2 size={18} /> : <span style={{
                            width: 22, height: 22, borderRadius: '50%', display: 'flex',
                            alignItems: 'center', justifyContent: 'center', fontSize: 12,
                            background: step === s.n ? 'rgba(255,255,255,0.3)' : '#e5e7eb',
                        }}>{s.n}</span>}
                        {s.label}
                    </div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* ── Workspaces Card ── */}
                <div className="card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>Workspaces</h3>

                    {/* Create new */}
                    <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                        <input
                            className="input"
                            placeholder="New workspace name..."
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                            style={{ flex: 1 }}
                        />
                        <button className="btn btn-primary" onClick={handleCreate} disabled={creating}
                            style={{ padding: '8px 14px', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Plus size={16} /> Create
                        </button>
                    </div>

                    {/* List */}
                    {workspaces.length === 0 ? (
                        <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: 16 }}>
                            No workspaces yet. Create one to get started!
                        </p>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {workspaces.map((ws) => (
                                <div
                                    key={ws.id}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: 8,
                                        padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                                        background: activeWorkspace?.id === ws.id ? 'var(--accent-light)' : 'var(--bg-input)',
                                        border: activeWorkspace?.id === ws.id ? '2px solid var(--accent)' : '2px solid transparent',
                                        transition: 'all 0.15s ease',
                                    }}
                                    onClick={() => setActiveWorkspace(ws)}
                                >
                                    <FolderOpen size={16} style={{ color: 'var(--accent)' }} />
                                    <span style={{ flex: 1, fontWeight: 600, fontSize: 13 }}>{ws.name}</span>
                                    {activeWorkspace?.id === ws.id && (
                                        <span className="badge badge-green" style={{ fontSize: 10 }}>Active</span>
                                    )}
                                    {confirmDeleteWs === ws.id ? (
                                        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }} onClick={(e) => e.stopPropagation()}>
                                            <span style={{ fontSize: 11, color: '#ef4444' }}>Delete?</span>
                                            <button
                                                onClick={() => { deleteWorkspace(ws.id); setConfirmDeleteWs(null); }}
                                                style={{ background: '#ef4444', color: '#fff', border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 11, cursor: 'pointer' }}
                                            >
                                                Yes
                                            </button>
                                            <button
                                                onClick={() => setConfirmDeleteWs(null)}
                                                style={{ background: '#e5e7eb', border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 11, cursor: 'pointer' }}
                                            >
                                                No
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setConfirmDeleteWs(ws.id); }}
                                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: 4 }}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Quick actions */}
                    {activeWorkspace && (
                        <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                            <button className="btn" onClick={() => navigate('/papers')}
                                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 12 }}>
                                <Upload size={14} /> Upload PDFs
                            </button>
                            <button className="btn btn-primary" onClick={() => navigate('/analysis')}
                                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 12 }}>
                                <Sparkles size={14} /> Analyze <ArrowRight size={14} />
                            </button>
                        </div>
                    )}
                </div>

                {/* ── History Card ── */}
                <div className="card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Clock size={16} /> Analysis History
                    </h3>

                    {!activeWorkspace ? (
                        <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: 16 }}>
                            Select a workspace to see history
                        </p>
                    ) : history.length === 0 ? (
                        <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: 16 }}>
                            No analyses yet. Run your first one!
                        </p>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {history.map((item) => (
                                <div
                                    key={item.id}
                                    style={{
                                        padding: '10px 12px', borderRadius: 8,
                                        background: 'var(--bg-input)', cursor: 'pointer',
                                        transition: 'background 0.15s',
                                    }}
                                    onClick={() => navigate(`/analysis?result=${item.id}`)}
                                >
                                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>{item.query}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                        {item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown date'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
