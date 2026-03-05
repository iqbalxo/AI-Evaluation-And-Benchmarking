import React, { useState } from 'react';
import Dashboard from './pages/Dashboard.jsx';
import Systems from './pages/Systems.jsx';
import Datasets from './pages/Datasets.jsx';
import Evaluations from './pages/Evaluations.jsx';
import Experiments from './pages/Experiments.jsx';

const NAV_ITEMS = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'systems', icon: '🤖', label: 'AI Systems' },
    { id: 'datasets', icon: '📁', label: 'Datasets' },
    { id: 'evaluations', icon: '🧪', label: 'Evaluations' },
    { id: 'experiments', icon: '⚗️', label: 'Experiments' },
];

const PAGES = {
    dashboard: Dashboard,
    systems: Systems,
    datasets: Datasets,
    evaluations: Evaluations,
    experiments: Experiments,
};

export default function App() {
    const [page, setPage] = useState('dashboard');
    const Page = PAGES[page] || Dashboard;

    return (
        <div className="app-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <h1>AI Eval Platform</h1>
                    <span>Benchmarking Suite</span>
                </div>
                <nav className="sidebar-nav">
                    {NAV_ITEMS.map(item => (
                        <button
                            key={item.id}
                            id={`nav-${item.id}`}
                            className={`nav-item${page === item.id ? ' active' : ''}`}
                            onClick={() => setPage(item.id)}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </button>
                    ))}
                </nav>
                <div style={{ padding: 'var(--space-md)', borderTop: '1px solid var(--glass-border)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    v1.0.0 • AI Eval Platform
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <Page key={page} />
            </main>
        </div>
    );
}
