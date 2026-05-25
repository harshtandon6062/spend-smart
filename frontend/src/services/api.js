import axios from 'axios';

const api = axios.create({
  baseURL: '',
  timeout: 15000,
});

/**
 * Upload a CSV file for analysis.
 * @param {File} file - The CSV file to upload
 * @returns {Promise<{analytics, recommendations}>}
 */
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

/**
 * Load bundled sample data.
 * @returns {Promise<{analytics, recommendations}>}
 */
export const loadSample = async () => {
  const res = await api.get('/api/sample');
  return res.data;
};

/**
 * Get analytics for current dataset.
 * @returns {Promise<AnalyticsResponse>}
 */
export const getAnalytics = async () => {
  const res = await api.get('/api/analytics');
  return res.data;
};

/**
 * Get recommendations for current dataset.
 * @returns {Promise<Insight[]>}
 */
export const getRecommendations = async () => {
  const res = await api.get('/api/recommendations');
  return res.data;
};

/**
 * Run a what-if savings simulation.
 * @param {Object} reductions - {category: percentReduction}
 * @returns {Promise<SimulationResponse>}
 */
export const simulate = async (reductions) => {
  const res = await api.post('/api/simulate', { reductions });
  return res.data;
};
