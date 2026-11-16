import { API_BASE, getMediaUrl, ENDPOINTS, BACKEND_URL } from './config';

export { getMediaUrl, BACKEND_URL, API_BASE };

const getAuthHeaders = (extraHeaders = {}) => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('brainsight_token') : null;
  const headers = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

export const api = {
  // Authentication & Users
  async register(name, email, password, role = 'clinician') {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Registration failed');
    if (data.token && typeof localStorage !== 'undefined') {
      localStorage.setItem('brainsight_token', data.token);
      localStorage.setItem('brainsight_user', JSON.stringify(data.user));
    }
    return data;
  },

  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Login failed');
    if (data.token && typeof localStorage !== 'undefined') {
      localStorage.setItem('brainsight_token', data.token);
      localStorage.setItem('brainsight_user', JSON.stringify(data.user));
    }
    return data;
  },

  async getCurrentUser() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return null;
    return res.json();
  },

  logout() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('brainsight_token');
      localStorage.removeItem('brainsight_user');
    }
  },

  // MongoDB & Database Diagnostics
  async getDatabaseStatus() {
    try {
      const res = await fetch(`${API_BASE}/database/status`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      return { success: false, error: e.message };
    }
  },

  // Backend health status check
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      return { status: 'error', message: err.message || 'Cannot reach backend server' };
    }
  },

  // Model status
  async getModelStatus() {
    const res = await fetch(`${API_BASE}/model/status`);
    if (!res.ok) throw new Error('Failed to get model status');
    return res.json();
  },

  // Dashboard analytics
  async getDashboardStats() {
    const res = await fetch(`${API_BASE}/dashboard/stats`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch dashboard statistics');
    return res.json();
  },

  // Upload MRI
  async uploadMRI(file, patientId = '') {
    const formData = new FormData();
    formData.append('file', file);
    if (patientId) {
      formData.append('patient_id', patientId);
    }
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Upload failed');
    }
    return res.json();
  },

  // Image Enhancement
  async enhanceMRI(scanId, params = {}) {
    const res = await fetch(`${API_BASE}/enhance`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        scan_id: scanId,
        ...params
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Enhancement failed');
    }
    return res.json();
  },

  // CNN Prediction & Grad-CAM
  async predictTumor(scanId, useEnhanced = false) {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        scan_id: scanId,
        use_enhanced: useEnhanced
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.message || data.error || 'Prediction failed');
    }
    return data;
  },

  // Generate Report
  async generateReport(scanId) {
    const res = await fetch(`${API_BASE}/generate-report`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ scan_id: scanId })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Report generation failed');
    }
    return res.json();
  },

  // Scan History
  async getHistory(category = 'All', search = '') {
    const params = new URLSearchParams();
    if (category && category !== 'All') params.append('category', category);
    if (search) params.append('search', search);

    const res = await fetch(`${API_BASE}/history?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to load history');
    return res.json();
  },

  // Get Single Scan
  async getScanDetails(scanId) {
    const res = await fetch(`${API_BASE}/history/${scanId}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to load scan details');
    return res.json();
  },

  // Delete Scan
  async deleteScan(scanId) {
    const res = await fetch(`${API_BASE}/history/${scanId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to delete scan');
    }
    return res.json();
  },

  // Sample images for testing
  async getSampleImages() {
    const res = await fetch(`${API_BASE}/sample-images`);
    if (!res.ok) return { samples: [] };
    return res.json();
  }
};
