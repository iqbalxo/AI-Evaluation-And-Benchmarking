import React, { useEffect, useState } from 'react';
import { getRuns, getRunDetail } from '../api.js';

export default function RunTracing() {
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [detail, setDetail] = useState(null);
    const [expandedTraceId, setExpandedTraceId] = useState(null);

    const load = async () => {
        const r = await getRuns();
        setRuns(r);
        setLoading(false);
    };

    useEffect(() => { load(); }, []);

    const showDetail = async (runId) => {
        if (detail?.id === runId) {
            setDetail(null);
            setExpandedTraceId(null);
            return;
        }
        setDetail(null);
        const d = await getRunDetail(runId);
        setDetail(d);
        setExpandedTraceId(null);
    };

    const toggleTrace = (traceId) => {
        setExpandedTraceId(prev => prev === traceId ? null : traceId);
    };

    if (loading) return <div className="spinner" />;

    return (
        <>
            <div className="page-header">
                <h2>🔍 Run Tracing</h2>
                <p>LangSmith-style observability: Inspect raw prompts, responses, judge evaluations, and token usage for every executed run.</p>
            </div>

            <div className="card section animate-in">
                <div className="chart-title">Evaluation Runs</div>
                {runs.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📡</div>
                        <p>No telemetry found. Run an evaluation to start tracking traces.</p>
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
                                    <th>Timestamp</th>
                                    <th>Traces</th>
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
                                            <td>{r.started_at ? new Date(r.started_at).toLocaleString() : '—'}</td>
                                            <td>{r.total_items} items</td>
                                            <td><button className="btn btn-outline btn-sm">{detail?.id === r.id ? '▲' : '▼'}</button></td>
                                        </tr>
                                        {/* TRACES PANEL EXPANDED */}
                                        {detail?.id === r.id && (
                                            <tr>
                                                <td colSpan={7} style={{ padding: 0, border: 'none' }}>
                                                    <div className="details-panel" style={{ margin: '0 8px 8px', backgroundColor: 'var(--bg-card)' }}>
                                                        <div className="chart-title" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                                                            Trace Breakdown for Run #{r.id}
                                                        </div>
                                                        {detail.results && detail.results.length > 0 ? (
                                                            <div className="traces-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                {detail.results.map(trace => (
                                                                    <div key={trace.id} className="trace-item" style={{ border: '1px solid var(--glass-border)', borderRadius: '8px', overflow: 'hidden' }}>

                                                                        {/* Trace Header (Clickable) */}
                                                                        <div
                                                                            onClick={() => toggleTrace(trace.id)}
                                                                            style={{
                                                                                padding: '12px 16px',
                                                                                background: 'rgba(255,255,255,0.02)',
                                                                                cursor: 'pointer',
                                                                                display: 'flex',
                                                                                justifyContent: 'space-between',
                                                                                alignItems: 'center'
                                                                            }}>
                                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                                                                <span style={{ fontWeight: 600, color: '#e2e8f0' }}>Item #{trace.item_id}</span>
                                                                                <span className={`badge badge-${trace.status === 'failed' ? 'failed' : 'success'}`}>
                                                                                    {trace.status === 'failed' ? 'Error' : 'Complete'}
                                                                                </span>
                                                                                <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                                                                                    {trace.latency_ms?.toFixed(0)} ms • {trace.token_usage || 0} tokens
                                                                                </span>
                                                                            </div>
                                                                            <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem' }}>
                                                                                <span style={{ color: trace.accuracy_score >= 7 ? '#10b981' : '#f43f5e' }}>Acc: {trace.accuracy_score}</span>
                                                                                <span style={{ color: trace.hallucination_flag ? '#f43f5e' : '#10b981' }}>Hal: {trace.hallucination_flag ? 'Yes' : 'No'}</span>
                                                                            </div>
                                                                        </div>

                                                                        {/* Trace Extended Details */}
                                                                        {expandedTraceId === trace.id && (
                                                                            <div style={{ padding: '16px', borderTop: '1px solid var(--glass-border)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

                                                                                {/* Left Column: Model Under Test */}
                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', marginBottom: '4px' }}>Model Context</div>
                                                                                        <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', fontSize: '0.85rem', color: '#cbd5e1' }}>
                                                                                            <strong>{trace.provider_name || 'System'}: </strong> {trace.model_name || 'Unknown'}
                                                                                        </div>
                                                                                    </div>

                                                                                    {trace.error_message && (
                                                                                        <div>
                                                                                            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#ef4444', marginBottom: '4px' }}>Exception Traceback</div>
                                                                                            <pre style={{ background: '#450a0a', padding: '10px', borderRadius: '6px', fontSize: '0.85rem', color: '#fca5a5', whiteSpace: 'pre-wrap' }}>
                                                                                                {trace.error_message}
                                                                                            </pre>
                                                                                        </div>
                                                                                    )}

                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', marginBottom: '4px' }}>Input Prompt</div>
                                                                                        <div style={{ background: '#1e293b', padding: '10px', borderRadius: '6px', fontSize: '0.85rem', color: '#cbd5e1', whiteSpace: 'pre-wrap' }}>
                                                                                            {trace.prompt || '—'}
                                                                                        </div>
                                                                                    </div>
                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', marginBottom: '4px' }}>Expected Output</div>
                                                                                        <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '10px', borderRadius: '6px', fontSize: '0.85rem', color: '#34d399', whiteSpace: 'pre-wrap' }}>
                                                                                            {trace.expected_output || '—'}
                                                                                        </div>
                                                                                    </div>
                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', marginBottom: '4px' }}>Raw Model Output</div>
                                                                                        <div style={{ background: '#1e293b', padding: '10px', borderRadius: '6px', fontSize: '0.85rem', color: '#e2e8f0', whiteSpace: 'pre-wrap' }}>
                                                                                            {trace.response || '(Empty or Failed)'}
                                                                                        </div>
                                                                                    </div>
                                                                                </div>

                                                                                {/* Right Column: Judge Trace */}
                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#8b5cf6', marginBottom: '4px' }}>Judge Evaluation Prompt</div>
                                                                                        <pre style={{ background: '#1e1b4b', border: '1px solid rgba(139, 92, 246, 0.2)', padding: '10px', borderRadius: '6px', fontSize: '0.75rem', color: '#c4b5fd', whiteSpace: 'pre-wrap', maxHeight: '250px', overflowY: 'auto' }}>
                                                                                            {trace.judge_prompt || '—'}
                                                                                        </pre>
                                                                                    </div>
                                                                                    <div>
                                                                                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#8b5cf6', marginBottom: '4px' }}>Judge Raw Telemetry</div>
                                                                                        <pre style={{ background: '#1e1b4b', border: '1px solid rgba(139, 92, 246, 0.2)', padding: '10px', borderRadius: '6px', fontSize: '0.75rem', color: '#a78bfa', whiteSpace: 'pre-wrap' }}>
                                                                                            {trace.judge_response || '—'}
                                                                                        </pre>
                                                                                    </div>
                                                                                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                                                                                        <div style={{ flex: 1, background: '#1e293b', padding: '10px', borderRadius: '6px' }}>
                                                                                            <span style={{ color: '#94a3b8', fontSize: '0.75rem', display: 'block' }}>Relevance</span>
                                                                                            <strong style={{ fontSize: '1.2rem', color: '#e2e8f0' }}>{trace.relevance_score}/10</strong>
                                                                                        </div>
                                                                                        <div style={{ flex: 1, background: '#1e293b', padding: '10px', borderRadius: '6px' }}>
                                                                                            <span style={{ color: '#94a3b8', fontSize: '0.75rem', display: 'block' }}>Reasoning</span>
                                                                                            <strong style={{ fontSize: '1.2rem', color: '#e2e8f0', textTransform: 'capitalize' }}>{trace.reasoning_quality}</strong>
                                                                                        </div>
                                                                                    </div>
                                                                                </div>

                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (
                                                            <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No trace data available for this run.</div>
                                                        )}
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
