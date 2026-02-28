import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard, FileSearch, FileText, GitGraph,
    Cpu, BarChart3, Search, Zap, Settings
} from 'lucide-react';

const NAV = [
    { to: '/', icon: LayoutDashboard, tip: 'Dashboard' },
    { to: '/analysis', icon: FileSearch, tip: 'Analysis' },
    { to: '/papers', icon: FileText, tip: 'Papers' },
    { to: '/paper-search', icon: Search, tip: 'Paper Search' },
    { to: '/graph', icon: GitGraph, tip: 'Knowledge Graph' },
    { to: '/agents', icon: Cpu, tip: 'Agents' },
    { to: '/insights', icon: BarChart3, tip: 'Insights' },
    { to: '/research-hub', icon: Zap, tip: 'Research Hub' },
];

export default function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="sidebar-logo">R</div>
            <nav className="sidebar-nav">
                {NAV.map(({ to, icon: Icon, tip }) => (
                    <NavLink key={to} to={to} end={to === '/'} className="sidebar-link" title={tip}>
                        <Icon size={20} />
                    </NavLink>
                ))}
            </nav>
            <div style={{ marginTop: 'auto', paddingBottom: 16 }}>
                <NavLink to="/settings" className="sidebar-link" title="Settings">
                    <Settings size={20} />
                </NavLink>
            </div>
        </aside>
    );
}
