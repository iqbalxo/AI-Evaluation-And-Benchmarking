import React, { useEffect, useState } from 'react';
import { getSystems, createSystem, deleteSystem, getModelPresets } from '../api.js';
import { CUSTOM_MODEL_VALUE, MODEL_QUALITY_OPTIONS } from '../modelPresets.js';

const EMPTY_FORM = {
    name: '',
    model_type: 'openrouter',
    provider: '',
    tier: '',
    api_endpoint: '',
    config_json: '{}',
};

function formFromPreset(preset) {
    if (!preset) return EMPTY_FORM;
    return {
        name: preset.name,
        model_type: 'openrouter',
        provider: preset.provider,
        tier: preset.tier,
        api_endpoint: preset.id,
        config_json: '{}',
    };
}

function getDefaultPreset(presets) {
    return presets.find(p => p.id === 'openai/gpt-4o-mini')
        || presets.find(p => p.quality === 'balanced')
        || presets[0];
}

export default function Systems() {
    const [systems, setSystems] = useState([]);
    const [modelPresets, setModelPresets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState(EMPTY_FORM);
    const [qualityFilter, setQualityFilter] = useState('balanced');
    const [selectedPresetId, setSelectedPresetId] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const load = async () => {
        const [systemData, presetData] = await Promise.all([
            getSystems(),
            getModelPresets().catch(() => []),
        ]);
        setSystems(systemData);
        setModelPresets(presetData);
        setLoading(false);

        const preset = getDefaultPreset(presetData);
        if (preset && !selectedPresetId && !form.api_endpoint) {
            setSelectedPresetId(preset.id);
            setForm(formFromPreset(preset));
        }
    };

    useEffect(() => { load(); }, []);

    const handlePresetChange = (value) => {
        setSelectedPresetId(value);
        if (value === CUSTOM_MODEL_VALUE) {
            setForm({
                ...EMPTY_FORM,
                tier: 'Custom',
                config_json: form.config_json || '{}',
            });
            return;
        }

        const preset = modelPresets.find(p => p.id === value);
        setForm(formFromPreset(preset));
    };

    const handleQualityChange = (value) => {
        setQualityFilter(value);
        const preset = modelPresets.find(p => p.quality === value);
        if (preset) {
            handlePresetChange(preset.id);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.name || !form.model_type || !form.api_endpoint) return;
        setSubmitting(true);
        try {
            await createSystem({
                ...form,
                api_endpoint: form.api_endpoint.trim(),
                config_json: form.config_json || '{}',
            });
            const preset = getDefaultPreset(modelPresets);
            setSelectedPresetId(preset?.id || '');
            setForm(formFromPreset(preset));
            await load();
        } finally { setSubmitting(false); }
    };

    const handleDelete = async (id) => {
        await deleteSystem(id);
        await load();
    };

    if (loading) return <div className="spinner" />;

    const filteredPresets = modelPresets.filter(p => p.quality === qualityFilter);
    const selectedPreset = modelPresets.find(p => p.id === selectedPresetId);
    const isCustomModel = selectedPresetId === CUSTOM_MODEL_VALUE;

    return (
        <>
            <div className="page-header">
                <h2>AI Systems</h2>
                <p>Register OpenRouter models for evaluation with balanced presets and custom model support</p>
            </div>

            {/* Registration Form */}
            <div className="card section animate-in">
                <div className="chart-title">Register New System</div>
                <form onSubmit={handleSubmit}>
                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="preset-quality">Preset Group</label>
                            <select id="preset-quality" value={qualityFilter} onChange={e => handleQualityChange(e.target.value)}>
                                {MODEL_QUALITY_OPTIONS.map(q => <option key={q} value={q}>{q}</option>)}
                            </select>
                        </div>
                        <div className="form-field">
                            <label htmlFor="sys-preset">OpenRouter Model</label>
                            <select id="sys-preset" value={selectedPresetId} onChange={e => handlePresetChange(e.target.value)}>
                                <option value="">Select a model preset...</option>
                                {filteredPresets.map(p => (
                                    <option key={p.id} value={p.id}>{p.name} ({p.provider})</option>
                                ))}
                                <option value={CUSTOM_MODEL_VALUE}>Custom OpenRouter model ID</option>
                            </select>
                        </div>
                    </div>

                    {selectedPreset && (
                        <div className="details-panel" style={{ marginBottom: 'var(--space-md)' }}>
                            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                                <span className="badge badge-running">{selectedPreset.provider}</span>
                                <span className="badge badge-completed">{selectedPreset.tier}</span>
                                <span className="badge badge-pending">Cost: {selectedPreset.cost_profile}</span>
                                <code style={{ color: 'var(--text-secondary)' }}>{selectedPreset.id}</code>
                            </div>
                            <p style={{ color: 'var(--text-secondary)', marginTop: 8, fontSize: '0.85rem' }}>{selectedPreset.recommended_for}</p>
                        </div>
                    )}

                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="sys-name">System Name</label>
                            <input id="sys-name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. GPT-4o Mini Benchmark" required />
                        </div>
                        <div className="form-field">
                            <label htmlFor="sys-endpoint">OpenRouter Model ID</label>
                            <input
                                id="sys-endpoint"
                                value={form.api_endpoint}
                                onChange={e => setForm({ ...form, api_endpoint: e.target.value })}
                                placeholder="openai/gpt-4o-mini"
                                disabled={!isCustomModel && Boolean(selectedPreset)}
                                required
                            />
                        </div>
                    </div>
                    {isCustomModel && (
                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="sys-provider">Provider</label>
                                <input id="sys-provider" value={form.provider} onChange={e => setForm({ ...form, provider: e.target.value })} placeholder="e.g. OpenAI, Anthropic, Google" />
                            </div>
                            <div className="form-field">
                                <label htmlFor="sys-tier">Tier</label>
                                <input id="sys-tier" value={form.tier} onChange={e => setForm({ ...form, tier: e.target.value })} placeholder="e.g. Balanced, Premium, Budget" />
                            </div>
                        </div>
                    )}
                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="sys-config">Optional Generation Config JSON</label>
                            <input
                                id="sys-config"
                                value={form.config_json}
                                onChange={e => setForm({ ...form, config_json: e.target.value })}
                                placeholder='{"temperature":0.2,"max_tokens":512}'
                            />
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={submitting} id="btn-register-system">
                        {submitting ? 'Registering...' : 'Register System'}
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
                                    <th>Provider</th>
                                    <th>Tier</th>
                                    <th>Model ID</th>
                                    <th>Created</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {systems.map(s => (
                                    <tr key={s.id}>
                                        <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>#{s.id}</td>
                                        <td style={{ color: 'var(--text-primary)' }}>{s.name}</td>
                                        <td><span className="badge badge-completed">{s.provider || s.model_type}</span></td>
                                        <td>{s.tier || '—'}</td>
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
