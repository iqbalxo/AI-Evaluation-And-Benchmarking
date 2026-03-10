import React, { useEffect, useState } from 'react';
import { getExperiments, createExperiment, deleteExperiment, compareExperiment, getRuns } from '../api.js';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
    ResponsiveContainer, Legend, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

const PALETTE = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#a78bfa'];

export default function Experiments() {
    const [experiments, setExperiments] = useState([]);
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ name: '', description: '', run_ids: [] });
    const [comparison, setComparison] = useState(null);
    const [activeExp, setActiveExp] = useState(null);

    const load = async () => {
        const [e, r] = await Promise.all([getExperiments(), getRuns()]);
        setExperiments(e); setRuns(r.filter(run => run.status === 'completed'));
        setLoading(false);
    };
    useEffect(() => { load(); }, []);

    const toggleRunId = (id) => {
        setForm(f => ({
            ...f,
            run_ids: f.run_ids.includes(id) ? f.run_ids.filter(x => x !== id) : [...f.run_ids, id],
        }));
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!form.name || form.run_ids.length === 0) return;
        await createExperiment(form);
        setForm({ name: '', description: '', run_ids: [] });
        await load();
    };

    const handleCompare = async (expId) => {
        if (activeExp === expId) { setActiveExp(null); setComparison(null); return; }
        const data = await compareExperiment(expId);
        setComparison(data);
        setActiveExp(expId);
    };

    const handleDelete = async (id) => {
        await deleteExperiment(id);
        if (activeExp === id) { setActiveExp(null); setComparison(null); }
        await load();
    };

    if (loading) return <div className="spinner" />;

    // Prepare comparison chart data
    const barData = comparison?.runs?.map((r, i) => ({
        name: r.system_name || `Run #${r.id}`,
        Accuracy: r.avg_accuracy || 0,
        Relevance: r.avg_relevance || 0,
        'Halluc. Rate': r.hallucination_rate || 0,
    })) || [];

    const radarCompareData = comparison?.runs?.length ?
        ['Accuracy', 'Relevance', 'Speed', 'Low Halluc.', 'Cost Eff.'].map(metric => {
            const obj = { metric };
            comparison.runs.forEach((r, i) => {
                const label = r.system_name || `Run #${r.id}`;
                if (metric === 'Accuracy') obj[label] = r.avg_accuracy || 0;
                else if (metric === 'Relevance') obj[label] = r.avg_relevance || 0;
                else if (metric === 'Speed') obj[label] = Math.max(0, 10 - (r.avg_latency_ms || 0) / 100);
                else if (metric === 'Low Halluc.') obj[label] = Math.max(0, 10 - (r.hallucination_rate || 0) / 10);
                else if (metric === 'Cost Eff.') obj[label] = Math.max(0, 10 - (r.total_cost || 0) * 100);
            });
            return obj;
        }) : [];

    return (
        <>
            <div className="page-header">
                <h2>Experiments</h2>
                <p>Compare evaluation runs side-by-side to find the best configuration</p>
            </div>

            {/* Create Experiment */}
            <div className="card section animate-in">
                <div className="chart-title">Create New Experiment</div>
                <form onSubmit={handleCreate}>
                    <div className="form-row">
                        <div className="form-field">
                            <label>Experiment Name</label>
                            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. GPT-4 vs Claude Comparison" required />
                        </div>
                        <div className="form-field">
                            <label>Description</label>
                            <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Brief description" />
                        </div>
                    </div>

                    {/* Run Selection */}
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Select Runs to Compare ({form.run_ids.length} selected)
                        </label>
                        {runs.length === 0 ? (
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No completed runs available. Go to Evaluations to create some first.</div>
                        ) : (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                {runs.map(r => (
                                    <button
                                        key={r.id}
                                        type="button"
                                        className={`btn btn-sm ${form.run_ids.includes(r.id) ? 'btn-primary' : 'btn-outline'}`}
                                        onClick={() => toggleRunId(r.id)}
                                    >
                                        #{r.id} {r.system_name} — Acc: {r.avg_accuracy?.toFixed(1)}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <button type="submit" className="btn btn-primary" disabled={form.run_ids.length === 0} id="btn-create-experiment">
                        ⚗️ Create Experiment
                    </button>
                </form>
            </div>

            {/* Experiment List */}
            {experiments.length > 0 && (
                <div className="card section animate-in">
                    <div className="chart-title">Experiments ({experiments.length})</div>
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Description</th>
                                    <th>Runs</th>
                                    <th>Created</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {experiments.map(exp => (
                                    <tr key={exp.id}>
                                        <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{exp.id}</td>
                                        <td style={{ color: 'var(--text-primary)' }}>{exp.name}</td>
                                        <td>{exp.description || '—'}</td>
                                        <td>{JSON.parse(exp.run_ids_json).length} runs</td>
                                        <td>{new Date(exp.created_at).toLocaleDateString()}</td>
                                        <td style={{ display: 'flex', gap: 6 }}>
                                            <button className="btn btn-primary btn-sm" onClick={() => handleCompare(exp.id)}>
                                                {activeExp === exp.id ? '▲ Hide' : '📊 Compare'}
                                            </button>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(exp.id)}>Delete</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Comparison Results */}
            {comparison && activeExp && (
                <div className="animate-in">
                    {/* Bar Chart Comparison */}
                    <div className="card section">
                        <div className="chart-title">Metric Comparison — {comparison.experiment.name}</div>
                        <div className="chart-container">
                            <ResponsiveContainer width="100%" height={320}>
                                <BarChart data={barData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                                    <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} />
                                    <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} />
                                    <ReTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                    <Bar dataKey="Accuracy" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Relevance" fill="#10b981" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Halluc. Rate" fill="#ef4444" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Radar Comparison */}
                    {radarCompareData.length > 0 && (
                        <div className="card section">
                            <div className="chart-title">Multi-Dimension Radar Comparison</div>
                            <div style={{ display: 'flex', justifyContent: 'center' }}>
                                <ResponsiveContainer width="100%" height={350}>
                                    <RadarChart data={radarCompareData}>
                                        <PolarGrid stroke="rgba(99,102,241,0.15)" />
                                        <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                        <PolarRadiusAxis domain={[0, 10]} tick={false} axisLine={false} />
                                        {comparison.runs.map((r, i) => (
                                            <Radar
                                                key={r.id}
                                                dataKey={r.system_name || `Run #${r.id}`}
                                                stroke={PALETTE[i % PALETTE.length]}
                                                fill={PALETTE[i % PALETTE.length]}
                                                fillOpacity={0.1}
                                                strokeWidth={2}
                                            />
                                        ))}
                                        <ReTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                                        <Legend wrapperStyle={{ fontSize: 12 }} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* Detail Table */}
                    <div className="card section">
                        <div className="chart-title">Detailed Run Metrics</div>
                        <div className="table-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Run</th>
                                        <th>System</th>
                                        <th>Tier</th>
                                        <th>Dataset</th>
                                        <th>Accuracy</th>
                                        <th>Relevance</th>
                                        <th>Halluc. %</th>
                                        <th>Latency</th>
                                        <th>Tokens (Avg)</th>
                                        <th>Cost</th>
                                        <th>Success</th>
                                        <th>Failed</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {comparison.runs.map(r => (
                                        <tr key={r.id}>
                                            <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{r.id}</td>
                                            <td>{r.system_name}
                                                {r.provider && <div style={{ fontSize: '0.7em', color: 'var(--text-muted)' }}>{r.provider}</div>}
                                            </td>
                                            <td>
                                                {r.tier ? <span className="badge" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>{r.tier}</span> : '—'}
                                            </td>
                                            <td>{r.dataset_name}</td>
                                            <td className={r.avg_accuracy >= 7 ? 'score-high' : r.avg_accuracy >= 4 ? 'score-mid' : 'score-low'}>{r.avg_accuracy?.toFixed(2) || '0.00'}</td>
                                            <td>{r.avg_relevance?.toFixed(2) || '0.00'}</td>
                                            <td>{r.hallucination_rate?.toFixed(1) || '0.0'}%</td>
                                            <td>{r.avg_latency_ms?.toFixed(0) || '0'} ms</td>
                                            <td>{r.avg_token_usage ? r.avg_token_usage.toFixed(0) : '0'}</td>
                                            <td>{r.total_cost != null ? `$${r.total_cost.toFixed(4)}` : <span style={{ color: 'var(--text-muted)' }}>N/A</span>}</td>
                                            <td><span className="badge badge-completed">{r.successful_runs || 0}</span></td>
                                            <td>{r.failed_runs > 0 ? <span className="badge badge-failed">{r.failed_runs}</span> : r.failed_runs || 0}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
