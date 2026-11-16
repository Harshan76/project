// Centralized API and Backend Configuration

export const BACKEND_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

// Relative or full API base. When BACKEND_URL is unset/empty, uses relative '/api' proxied by Vite
export const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

/**
 * Normalizes media asset URLs (uploads, enhanced images, reports, sample MRIs)
 * so they resolve cleanly regardless of host or port.
 */
export function getMediaUrl(path) {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:') || path.startsWith('blob:')) {
    return path;
  }
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (BACKEND_URL) {
    return `${BACKEND_URL}${cleanPath}`;
  }
  return cleanPath;
}

export const ENDPOINTS = {
  HEALTH: `${API_BASE}/health`,
  MODEL_STATUS: `${API_BASE}/model/status`,
  DASHBOARD_STATS: `${API_BASE}/dashboard/stats`,
  UPLOAD: `${API_BASE}/upload`,
  ENHANCE: `${API_BASE}/enhance`,
  PREDICT: `${API_BASE}/predict`,
  REPORT: `${API_BASE}/generate-report`,
  HISTORY: `${API_BASE}/history`,
  SAMPLE_IMAGES: `${API_BASE}/sample-images`
};
