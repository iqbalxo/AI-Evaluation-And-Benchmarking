/**
 * Centralized API client for the AI Evaluation & Benchmarking Platform.
 * All fetch calls go through here for consistency.
 */

const BASE = '/api';

async function request(path, opts = {}) {
    const url = `${BASE}${path}`;
    const config = {
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
    };
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }
    const res = await fetch(url, config);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// ── AI Systems ──
export const getSystems = () => request('/systems/');
export const createSystem = (data) => request('/systems/', { method: 'POST', body: data });
export const deleteSystem = (id) => request(`/systems/${id}`, { method: 'DELETE' });

// ── Datasets ──
export const getDatasets = () => request('/datasets/');
export const createDataset = (data) => request('/datasets/', { method: 'POST', body: data });
export const deleteDataset = (id) => request(`/datasets/${id}`, { method: 'DELETE' });
export const getDatasetItems = (id) => request(`/datasets/${id}/items`);
export const addDatasetItem = (id, data) => request(`/datasets/${id}/items`, { method: 'POST', body: data });
export const addDatasetItemsBatch = (id, items) => request(`/datasets/${id}/items/batch`, { method: 'POST', body: items });

// ── Evaluations ──
export const triggerRun = (data) => request('/evaluations/run', { method: 'POST', body: data });
export const getRuns = () => request('/evaluations/runs');
export const getRunDetail = (id) => request(`/evaluations/runs/${id}`);
export const getStats = () => request('/evaluations/stats');

// ── Experiments ──
export const getExperiments = () => request('/experiments/');
export const createExperiment = (data) => request('/experiments/', { method: 'POST', body: data });
export const compareExperiment = (id) => request(`/experiments/${id}/compare`);
export const deleteExperiment = (id) => request(`/experiments/${id}`, { method: 'DELETE' });
