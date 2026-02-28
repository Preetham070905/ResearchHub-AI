import { useState, useEffect, useRef, type DragEvent, type ChangeEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import type { PaperItem } from '../types/api';
import { Upload, FileText, Trash2, AlertCircle, Download } from 'lucide-react';

export default function PapersPage() {
    const { activeWorkspace } = useAuth();
    const [papers, setPapers] = useState<PaperItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [dragOver, setDragOver] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const loadPapers = async () => {
        if (!activeWorkspace) return;
        setLoading(true);
        try {
            const data = await api.listPapers(activeWorkspace.id);
            setPapers(data);
        } catch {
            setError('Failed to load papers');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPapers();
    }, [activeWorkspace]);

    const handleUpload = async (files: FileList | null) => {
        if (!files || !activeWorkspace) return;
        setUploading(true);
        setError('');

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file.name.endsWith('.pdf')) {
                setError(`"${file.name}" is not a PDF file`);
                continue;
            }
            if (file.size > 50 * 1024 * 1024) {
                setError(`"${file.name}" exceeds 50 MB limit`);
                continue;
            }
            try {
                await api.uploadPaper(activeWorkspace.id, file);
            } catch {
                setError(`Failed to upload "${file.name}"`);
            }
        }
        setUploading(false);
        await loadPapers();
    };

    const handleDelete = async (paperId: number) => {
        if (!activeWorkspace) return;
        try {
            await api.deletePaper(activeWorkspace.id, paperId);
            setConfirmDelete(null);
            await loadPapers();
        } catch {
            setError('Failed to delete paper');
        }
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        handleUpload(e.dataTransfer.files);
    };

    const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
        handleUpload(e.target.files);
        e.target.value = '';
    };

    if (!activeWorkspace) {
        return (
            <div className="page-content">
                <div className="card" style={{ padding: 40, textAlign: 'center' }}>
                    <AlertCircle size={32} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
                    <p style={{ color: 'var(--text-muted)' }}>
                        Select a workspace from the Dashboard first to manage papers.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="page-content">
            <h2 style={{ marginBottom: 20, fontSize: 20, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                <FileText size={22} style={{ color: 'var(--accent)' }} />
                Papers — {activeWorkspace.name}
            </h2>

            {error && <div className="error-msg" style={{ marginBottom: 16 }}>{error}</div>}

            {/* Upload Zone */}
            <div
                className="card"
                style={{
                    padding: 40,
                    textAlign: 'center',
                    borderStyle: dragOver ? 'solid' : 'dashed',
                    borderColor: dragOver ? 'var(--accent)' : '#d1d5db',
                    borderWidth: 2,
                    background: dragOver ? 'var(--accent-light)' : 'var(--bg-card)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    marginBottom: 20,
                }}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    multiple
                    style={{ display: 'none' }}
                    onChange={handleFileSelect}
                />
                <Upload size={36} style={{ color: dragOver ? 'var(--accent)' : 'var(--text-muted)', marginBottom: 12 }} />
                <p style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                    {uploading ? 'Uploading...' : 'Drop PDFs here or click to browse'}
                </p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Supports .pdf files up to 50 MB each
                </p>
            </div>

            {/* Papers List */}
            <div className="card" style={{ padding: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
                    Uploaded Papers ({papers.length})
                </h3>

                {loading ? (
                    <div className="loading-overlay" style={{ padding: 30 }}>
                        <div className="spinner" />
                    </div>
                ) : papers.length === 0 ? (
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>
                        No papers uploaded yet. Drag & drop PDFs above!
                    </p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {papers.map((paper) => (
                            <div
                                key={paper.id}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 10,
                                    padding: '10px 14px',
                                    borderRadius: 8,
                                    background: 'var(--bg-input)',
                                    fontSize: 13,
                                }}
                            >
                                <FileText size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                <span style={{ flex: 1, fontWeight: 500 }}>{paper.filename}</span>
                                <span className="badge badge-blue">ID: {paper.id}</span>

                                <a
                                    href={api.getDownloadUrl(activeWorkspace.id, paper.id)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', padding: 4 }}
                                    title="Download"
                                >
                                    <Download size={14} />
                                </a>

                                {confirmDelete === paper.id ? (
                                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                                        <span style={{ fontSize: 11, color: '#ef4444' }}>Delete?</span>
                                        <button
                                            onClick={() => handleDelete(paper.id)}
                                            style={{ background: '#ef4444', color: '#fff', border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 11, cursor: 'pointer' }}
                                        >
                                            Yes
                                        </button>
                                        <button
                                            onClick={() => setConfirmDelete(null)}
                                            style={{ background: '#e5e7eb', border: 'none', borderRadius: 4, padding: '2px 8px', fontSize: 11, cursor: 'pointer' }}
                                        >
                                            No
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setConfirmDelete(paper.id)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', padding: 4 }}
                                        title="Delete paper"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
