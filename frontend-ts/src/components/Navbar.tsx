import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Search, Sparkles, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
    const { workspaces, activeWorkspace, setActiveWorkspace, email, logout } = useAuth();
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');

    const handleSearch = () => {
        if (!searchQuery.trim()) return;
        navigate(`/paper-search?q=${encodeURIComponent(searchQuery.trim())}`);
        setSearchQuery('');
    };

    return (
        <nav className="navbar">
            <div className="navbar-left">
                <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-heading)' }}>ResearchAI</span>

                {/* Workspace selector */}
                <select
                    className="input"
                    style={{ width: 160, fontSize: 12, padding: '6px 10px' }}
                    value={activeWorkspace?.id ?? ''}
                    onChange={(e) => {
                        const ws = workspaces.find((w) => w.id === Number(e.target.value));
                        if (ws) setActiveWorkspace(ws);
                    }}
                >
                    <option value="" disabled>Select workspace</option>
                    {workspaces.map((ws) => (
                        <option key={ws.id} value={ws.id}>{ws.name}</option>
                    ))}
                </select>
            </div>

            <div className="navbar-center">
                <div style={{ position: 'relative', width: 320 }}>
                    <Search size={14} style={{
                        position: 'absolute', left: 10, top: '50%',
                        transform: 'translateY(-50%)', color: 'var(--text-muted)',
                    }} />
                    <input
                        className="input"
                        placeholder="Search papers across arXiv & PubMed..."
                        style={{ width: '100%', paddingLeft: 32, fontSize: 12 }}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                </div>
            </div>

            <div className="navbar-right" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <button
                    className="btn btn-primary"
                    style={{ fontSize: 12, padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 5 }}
                    onClick={() => navigate('/analysis')}
                >
                    <Sparkles size={14} /> Run Agents
                </button>

                <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: 'var(--accent)', color: '#fff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: 13, cursor: 'pointer',
                }}
                    title={email ?? 'User'}
                >
                    {email ? email[0].toUpperCase() : 'U'}
                </div>

                <button
                    onClick={logout}
                    style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: 'var(--text-muted)', padding: 4,
                    }}
                    title="Logout"
                >
                    <LogOut size={18} />
                </button>
            </div>
        </nav>
    );
}
