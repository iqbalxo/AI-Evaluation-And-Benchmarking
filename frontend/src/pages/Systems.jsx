import React, { useEffect, useState } from 'react';
import { getSystems, createSystem, deleteSystem } from '../api.js';

export default function Systems() {
    const [systems, setSystems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ name: '', model_type: '', api_endpoint: '' });
    const [submitting, setSubmitting] = useState(false);

    const load = () => getSystems().then(setSystems).finally(() => setLoading(false));
    useEffect(() => { load(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.name || !form.model_type) return;
        setSubmitting(true);
        try {
            await createSystem(form);
            setForm({ name: '', model_type: '', api_endpoint: '' });
            await load();
        } finally { setSubmitting(false); }
    };

    const handleDelete = async (id) => {
        await deleteSystem(id);
        await load();
    };

    if (loading) return <div className="spinner" />;

    return (
        <>
            <div className="page-header">
                <h2>AI Systems</h2>
                <p>Register and manage AI applications for evaluation</p>
            </div>

            {/* Registration Form */}
            <div className="card section animate-in">
                <div className="chart-title">Register New System</div>
                <form onSubmit={handleSubmit}>
                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="sys-name">System Name</label>
                            <input id="sys-name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. GPT-4 Agent" required />
                        </div>
                        <div className="form-field">
                            <label htmlFor="sys-model">Model Type</label>
                            <input id="sys-model" value={form.model_type} onChange={e => setForm({ ...form, model_type: e.target.value })} placeholder="e.g. gpt-4, claude-3" required />
                        </div>
                        <div className="form-field">
                            <label htmlFor="sys-endpoint">API Endpoint</label>
                            <input id="sys-endpoint" value={form.api_endpoint} onChange={e => setForm({ ...form, api_endpoint: e.target.value })} placeholder="https://api.example.com/v1" />
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={submitting} id="btn-register-system">
                        {submitting ? '⏳ Registering…' : '➕ Register System'}
                    </button>
                </form>
            </div>

            {/* Systems List */}
            <div className="card section animate-in">
                <div className="chart-title">Registered Systems ({systems.length})</div>
                {systems.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🤖</div>
                        <p>No AI systems registered yet. Use the form above to add one.</p>
                    </div>
                ) : (
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Model Type</th>
                                    <th>Endpoint</th>
                                    <th>Created</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {systems.map(s => (
                                    <tr key={s.id}>
                                        <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{s.id}</td>
                                        <td style={{ color: 'var(--text-primary)' }}>{s.name}</td>
                                        <td><span className="badge badge-completed">{s.model_type}</span></td>
                                        <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.api_endpoint || '—'}</td>
                                        <td>{new Date(s.created_at).toLocaleDateString()}</td>
                                        <td><button className="btn btn-danger btn-sm" onClick={() => handleDelete(s.id)}>Delete</button></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </>
    );
}
