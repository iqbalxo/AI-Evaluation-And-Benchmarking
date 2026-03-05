import React, { useEffect, useState } from 'react';
import { getStats, getRuns } from '../api.js';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
    ResponsiveContainer, BarChart, Bar, Legend
} from 'recharts';

const COLORS = { accuracy: '#6366f1', latency: '#06b6d4', hallucination: '#ef4444', relevance: '#10b981' };

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([getStats(), getRuns()])
            .then(([s, r]) => { setStats(s); setRuns(r); })
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="spinner" />;

    const kpis = [
        { label: 'AI Systems', value: stats?.total_systems ?? 0, sub: 'Registered' },
        { label: 'Datasets', value: stats?.total_datasets ?? 0, sub: 'Available' },
        { label: 'Eval Runs', value: stats?.total_runs ?? 0, sub: 'Executed' },
        { label: 'Avg Accuracy', value: stats?.avg_accuracy?.toFixed(1) ?? '—', sub: 'Out of 10' },
    ];

    const trend = stats?.trend || [];

    return (
        <>
            <div className="page-header">
                <h2>Dashboard</h2>
                <p>Overview of your AI evaluation activity</p>
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid">
                {kpis.map((k, i) => (
                    <div key={i} className="card kpi-card animate-in">
                        <div className="kpi-label">{k.label}</div>
                        <div className="kpi-value">{k.value}</div>
                        <div className="kpi-sub">{k.sub}</div>
                    </div>
                ))}
            </div>

            {/* Performance Trend */}
            {trend.length > 0 && (
                <div className="card section animate-in">
                    <div className="chart-title">Performance Trend – Recent Runs</div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={trend}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                                <XAxis dataKey="run_id" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} label={{ value: 'Run ID', position: 'insideBottom', offset: -4, fill: '#64748b', fontSize: 11 }} />
                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} domain={[0, 10]} />
                                <ReTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                <Line type="monotone" dataKey="accuracy" stroke={COLORS.accuracy} strokeWidth={2} dot={{ r: 4 }} name="Accuracy" />
                                <Line type="monotone" dataKey="relevance" stroke={COLORS.relevance} strokeWidth={2} dot={{ r: 3 }} name="Relevance" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Hallucination & Latency bar chart */}
            {trend.length > 0 && (
                <div className="card section animate-in">
                    <div className="chart-title">Hallucination Rate & Latency</div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={260}>
                            <BarChart data={trend}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                                <XAxis dataKey="run_id" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} />
                                <YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 11 }} tickLine={false} label={{ value: '% / ms', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                                <ReTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                                <Legend wrapperStyle={{ fontSize: 12 }} />
                                <Bar yAxisId="left" dataKey="hallucination_rate" fill={COLORS.hallucination} name="Hallucination %" radius={[4, 4, 0, 0]} />
                                <Bar yAxisId="left" dataKey="latency" fill={COLORS.latency} name="Latency (ms)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Recent Runs Table */}
            <div className="card section animate-in">
                <div className="chart-title">Recent Evaluation Runs</div>
                {runs.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🧪</div>
                        <p>No evaluation runs yet. Go to Evaluations to trigger your first run.</p>
                    </div>
                ) : (
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Run ID</th>
                                    <th>System</th>
                                    <th>Dataset</th>
                                    <th>Status</th>
                                    <th>Accuracy</th>
                                    <th>Latency</th>
                                    <th>Halluc. Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                {runs.slice(0, 10).map(r => (
                                    <tr key={r.id}>
                                        <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{r.id}</td>
                                        <td>{r.system_name || '—'}</td>
                                        <td>{r.dataset_name || '—'}</td>
                                        <td><span className={`badge badge-${r.status}`}>{r.status}</span></td>
                                        <td className={r.avg_accuracy >= 7 ? 'score-high' : r.avg_accuracy >= 4 ? 'score-mid' : 'score-low'}>
                                            {r.avg_accuracy?.toFixed(1) ?? '—'}
                                        </td>
                                        <td>{r.avg_latency_ms?.toFixed(0) ?? '—'} ms</td>
                                        <td>{r.hallucination_rate?.toFixed(1) ?? '—'}%</td>
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
