import React, { useEffect, useState } from 'react';
import { getSystems, getDatasets, triggerRun, getRuns, getRunDetail } from '../api.js';
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    ResponsiveContainer, Tooltip as ReTooltip,
} from 'recharts';

export default function Evaluations() {
    const [systems, setSystems] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ system_id: '', dataset_id: '' });
    const [submitting, setSubmitting] = useState(false);
    const [detail, setDetail] = useState(null);

    const load = async () => {
        const [s, d, r] = await Promise.all([getSystems(), getDatasets(), getRuns()]);
        setSystems(s); setDatasets(d); setRuns(r);
        setLoading(false);
    };
    useEffect(() => { load(); }, []);

    const handleRun = async (e) => {
        e.preventDefault();
        if (!form.system_id || !form.dataset_id) return;
        setSubmitting(true);
        try {
            await triggerRun({ system_id: parseInt(form.system_id), dataset_id: parseInt(form.dataset_id) });
            // Wait a bit for background task, then refresh
            setTimeout(async () => {
                await load();
                setSubmitting(false);
            }, 2000);
        } catch {
            setSubmitting(false);
        }
    };

    const showDetail = async (runId) => {
        if (detail?.id === runId) { setDetail(null); return; }
        const d = await getRunDetail(runId);
        setDetail(d);
    };

    if (loading) return <div className="spinner" />;

    const radarData = detail ? [
        { metric: 'Accuracy', value: detail.avg_accuracy || 0, max: 10 },
        { metric: 'Relevance', value: detail.avg_relevance || 0, max: 10 },
        { metric: 'Low Halluc.', value: Math.max(0, 10 - (detail.hallucination_rate || 0) / 10), max: 10 },
        { metric: 'Speed', value: Math.max(0, 10 - (detail.avg_latency_ms || 0) / 100), max: 10 },
        { metric: 'Cost Eff.', value: Math.max(0, 10 - (detail.total_cost || 0) * 100), max: 10 },
    ] : [];

    return (
        <>
            <div className="page-header">
                <h2>Evaluations</h2>
                <p>Run evaluation pipelines and inspect results</p>
            </div>

            {/* Trigger Run */}
            <div className="card section animate-in">
                <div className="chart-title">Trigger New Evaluation Run</div>
                <form onSubmit={handleRun}>
                    <div className="form-row">
                        <div className="form-field">
                            <label>AI System</label>
                            <select value={form.system_id} onChange={e => setForm({ ...form, system_id: e.target.value })} required id="select-system">
                                <option value="">Select a system…</option>
                                {systems.map(s => <option key={s.id} value={s.id}>{s.name} ({s.model_type})</option>)}
                            </select>
                        </div>
                        <div className="form-field">
                            <label>Dataset</label>
                            <select value={form.dataset_id} onChange={e => setForm({ ...form, dataset_id: e.target.value })} required id="select-dataset">
                                <option value="">Select a dataset…</option>
                                {datasets.map(d => <option key={d.id} value={d.id}>{d.name} ({d.item_count} items)</option>)}
                            </select>
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={submitting} id="btn-trigger-run">
                        {submitting ? '⏳ Running evaluation…' : '🚀 Run Evaluation'}
                    </button>
                </form>
            </div>

            {/* Runs List */}
            <div className="card section animate-in">
                <div className="chart-title">Evaluation Runs ({runs.length})</div>
                {runs.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🧪</div>
                        <p>No runs yet. Select a system and dataset above to start.</p>
                    </div>
                ) : (
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Run</th>
                                    <th>System</th>
                                    <th>Dataset</th>
                                    <th>Status</th>
                                    <th>Accuracy</th>
                                    <th>Halluc. %</th>
                                    <th>Latency</th>
                                    <th>Cost</th>
                                    <th>Items</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {runs.map(r => (
                                    <React.Fragment key={r.id}>
                                        <tr onClick={() => showDetail(r.id)} style={{ cursor: 'pointer' }}>
                                            <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{r.id}</td>
                                            <td>{r.system_name || '—'}</td>
                                            <td>{r.dataset_name || '—'}</td>
                                            <td><span className={`badge badge-${r.status}`}>{r.status}</span></td>
                                            <td className={r.avg_accuracy >= 7 ? 'score-high' : r.avg_accuracy >= 4 ? 'score-mid' : 'score-low'}>{r.avg_accuracy?.toFixed(1) ?? '—'}</td>
                                            <td>{r.hallucination_rate?.toFixed(1) ?? '—'}%</td>
                                            <td>{r.avg_latency_ms?.toFixed(0) ?? '—'} ms</td>
                                            <td>${r.total_cost?.toFixed(4) ?? '—'}</td>
                                            <td>{r.total_items}</td>
                                            <td><button className="btn btn-outline btn-sm">{detail?.id === r.id ? '▲' : '▼'}</button></td>
                                        </tr>
                                        {detail?.id === r.id && (
                                            <tr>
                                                <td colSpan={10} style={{ padding: 0, border: 'none' }}>
                                                    <div className="details-panel" style={{ margin: '0 8px 8px' }}>
                                                        {/* Radar Chart */}
                                                        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                                                            <div style={{ flex: '0 0 300px' }}>
                                                                <div className="chart-title" style={{ fontSize: '0.8rem' }}>Quality Radar</div>
                                                                <ResponsiveContainer width={300} height={220}>
                                                                    <RadarChart data={radarData}>
                                                                        <PolarGrid stroke="rgba(99,102,241,0.15)" />
                                                                        <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                                                        <PolarRadiusAxis domain={[0, 10]} tick={false} axisLine={false} />
                                                                        <Radar dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
                                                                        <ReTooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                                                                    </RadarChart>
                                                                </ResponsiveContainer>
                                                            </div>
                                                            <div style={{ flex: 1, minWidth: 300 }}>
                                                                <div className="chart-title" style={{ fontSize: '0.8rem' }}>Per-Item Results</div>
                                                                <div className="table-wrapper">
                                                                    <table>
                                                                        <thead>
                                                                            <tr>
                                                                                <th>Prompt (item)</th>
                                                                                <th>Accuracy</th>
                                                                                <th>Halluc.</th>
                                                                                <th>Quality</th>
                                                                                <th>Relevance</th>
                                                                                <th>Latency</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                                            {detail.results?.map(res => (
                                                                                <tr key={res.id}>
                                                                                    <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Item #{res.item_id}</td>
                                                                                    <td className={res.accuracy_score >= 7 ? 'score-high' : res.accuracy_score >= 4 ? 'score-mid' : 'score-low'}>{res.accuracy_score}</td>
                                                                                    <td>{res.hallucination_flag ? '⚠️ Yes' : '✅ No'}</td>
                                                                                    <td>{res.reasoning_quality}</td>
                                                                                    <td>{res.relevance_score}</td>
                                                                                    <td>{res.latency_ms?.toFixed(0)} ms</td>
                                                                                </tr>
                                                                            ))}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </>
    );
}
