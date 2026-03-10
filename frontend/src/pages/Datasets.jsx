import React, { useEffect, useState } from 'react';
import { getDatasets, createDataset, deleteDataset, getDatasetItems, addDatasetItem, uploadDataset } from '../api.js';

export default function Datasets() {
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ name: '', description: '' });
    const [expanded, setExpanded] = useState(null);
    const [items, setItems] = useState([]);
    const [itemForm, setItemForm] = useState({ prompt: '', expected_output: '', evaluation_type: 'question_answering', difficulty: 'medium' });
    const [uploadFile, setUploadFile] = useState(null);
    const [uploading, setUploading] = useState(false);

    const load = () => getDatasets().then(setDatasets).finally(() => setLoading(false));
    useEffect(() => { load(); }, []);

    const handleCreateDataset = async (e) => {
        e.preventDefault();
        if (!form.name) return;
        await createDataset(form);
        setForm({ name: '', description: '' });
        await load();
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!uploadFile) return;
        setUploading(true);
        try {
            await uploadDataset(uploadFile);
            setUploadFile(null);
            document.getElementById('upload-input').value = "";
            await load();
        } catch (err) {
            alert(err.message);
        } finally {
            setUploading(false);
        }
    };

    const handleExpand = async (id) => {
        if (expanded === id) { setExpanded(null); return; }
        setExpanded(id);
        const data = await getDatasetItems(id);
        setItems(data);
    };

    const handleAddItem = async (e) => {
        e.preventDefault();
        if (!itemForm.prompt || !itemForm.expected_output) return;
        await addDatasetItem(expanded, itemForm);
        setItemForm({ prompt: '', expected_output: '', evaluation_type: 'question_answering', difficulty: 'medium' });
        const data = await getDatasetItems(expanded);
        setItems(data);
        await load();
    };

    const handleDelete = async (id) => {
        await deleteDataset(id);
        if (expanded === id) setExpanded(null);
        await load();
    };

    if (loading) return <div className="spinner" />;

    return (
        <>
            <div className="page-header">
                <h2>Evaluation Datasets</h2>
                <p>Create and manage benchmark datasets for AI evaluation</p>
            </div>

            {/* Create Dataset */}
            <div className="card section animate-in" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '1.5rem' }}>
                <div>
                    <div className="chart-title">Create Manual Dataset</div>
                    <form onSubmit={handleCreateDataset}>
                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="ds-name">Dataset Name</label>
                                <input id="ds-name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. QA Benchmark v1" required />
                            </div>
                            <div className="form-field">
                                <label htmlFor="ds-desc">Description</label>
                                <input id="ds-desc" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Brief description" />
                            </div>
                        </div>
                        <button type="submit" className="btn btn-primary" id="btn-create-dataset">➕ Create Dataset</button>
                    </form>
                </div>

                <div style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '1.5rem' }}>
                    <div className="chart-title">Upload Existing Dataset</div>
                    <form onSubmit={handleUpload}>
                        <div className="form-field">
                            <label>Upload CSV or JSON file</label>
                            <input
                                id="upload-input"
                                type="file"
                                accept=".csv,.json"
                                onChange={e => setUploadFile(e.target.files[0])}
                                style={{
                                    padding: '0.5rem',
                                    border: '1px dashed var(--glass-border)',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.02)',
                                    width: '100%',
                                    color: 'var(--text-secondary)'
                                }}
                                required
                            />
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                                Required columns/keys: <code>prompt</code>, <code>expected_output</code> (or <code>expected</code>).
                            </div>
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={uploading || !uploadFile} style={{ marginTop: '0.5rem' }}>
                            {uploading ? '⏳ Uploading...' : '⬆️ Upload Dataset'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Dataset List */}
            {datasets.length === 0 ? (
                <div className="card section animate-in">
                    <div className="empty-state">
                        <div className="empty-state-icon">📁</div>
                        <p>No datasets yet. Create your first benchmark dataset above.</p>
                    </div>
                </div>
            ) : (
                datasets.map(d => (
                    <div key={d.id} className="card section animate-in" style={{ cursor: 'pointer' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }} onClick={() => handleExpand(d.id)}>
                            <div>
                                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>📁 {d.name}</div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                    {d.description || 'No description'} • {d.item_count} items
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="btn btn-outline btn-sm" onClick={(e) => { e.stopPropagation(); handleExpand(d.id); }}>
                                    {expanded === d.id ? '▲ Collapse' : '▼ Expand'}
                                </button>
                                <button className="btn btn-danger btn-sm" onClick={(e) => { e.stopPropagation(); handleDelete(d.id); }}>Delete</button>
                            </div>
                        </div>

                        {expanded === d.id && (
                            <div className="details-panel" style={{ marginTop: 16 }}>
                                {/* Add Item Form */}
                                <div className="chart-title" style={{ fontSize: '0.82rem' }}>Add Test Item</div>
                                <form onSubmit={handleAddItem}>
                                    <div className="form-row">
                                        <div className="form-field" style={{ flex: 2 }}>
                                            <label>Prompt</label>
                                            <input value={itemForm.prompt} onChange={e => setItemForm({ ...itemForm, prompt: e.target.value })} placeholder="e.g. What is machine learning?" required />
                                        </div>
                                        <div className="form-field" style={{ flex: 2 }}>
                                            <label>Expected Output</label>
                                            <input value={itemForm.expected_output} onChange={e => setItemForm({ ...itemForm, expected_output: e.target.value })} placeholder="e.g. Machine learning is a subset of AI" required />
                                        </div>
                                    </div>
                                    <div className="form-row">
                                        <div className="form-field">
                                            <label>Type</label>
                                            <select value={itemForm.evaluation_type} onChange={e => setItemForm({ ...itemForm, evaluation_type: e.target.value })}>
                                                <option value="question_answering">Question Answering</option>
                                                <option value="rag_validation">RAG Validation</option>
                                                <option value="tool_usage">Tool Usage</option>
                                                <option value="classification">Classification</option>
                                            </select>
                                        </div>
                                        <div className="form-field">
                                            <label>Difficulty</label>
                                            <select value={itemForm.difficulty} onChange={e => setItemForm({ ...itemForm, difficulty: e.target.value })}>
                                                <option value="easy">Easy</option>
                                                <option value="medium">Medium</option>
                                                <option value="hard">Hard</option>
                                            </select>
                                        </div>
                                        <div className="form-field" style={{ display: 'flex', alignItems: 'flex-end' }}>
                                            <button type="submit" className="btn btn-primary btn-sm">Add Item</button>
                                        </div>
                                    </div>
                                </form>

                                {/* Items Table */}
                                {items.length > 0 && (
                                    <div className="table-wrapper" style={{ marginTop: 12 }}>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>#</th>
                                                    <th>Prompt</th>
                                                    <th>Expected Output</th>
                                                    <th>Type</th>
                                                    <th>Difficulty</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {items.map((item, i) => (
                                                    <tr key={item.id}>
                                                        <td>{i + 1}</td>
                                                        <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.prompt}</td>
                                                        <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.expected_output}</td>
                                                        <td><span className="badge badge-completed">{item.evaluation_type}</span></td>
                                                        <td>{item.difficulty}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))
            )}
        </>
    );
}
