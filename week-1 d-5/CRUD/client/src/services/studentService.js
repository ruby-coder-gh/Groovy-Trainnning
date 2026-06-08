import axios from 'axios';

const api = axios.create({ baseURL: '/api/v1', headers: { 'Content-Type': 'application/json' }, timeout: 10000 });

api.interceptors.response.use(
  (res) => res.data,
  (error) => {
    const msg = error.response?.data?.error?.message || 'Something went wrong';
    const details = error.response?.data?.error?.details || null;
    const code = error.response?.data?.error?.code || 'UNKNOWN_ERROR';
    const err = new Error(msg);
    err.code = code;
    err.details = details;
    err.status = error.response?.status;
    return Promise.reject(err);
  }
);

export const studentService = {
  getAll: (params = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.set('page', params.page);
    if (params.limit) q.set('limit', params.limit);
    if (params.search) q.set('search', params.search);
    if (params.status) q.set('status', params.status);
    if (params.major) q.set('major', params.major);
    if (params.sortBy) q.set('sortBy', params.sortBy);
    if (params.sortOrder) q.set('sortOrder', params.sortOrder);
    const qs = q.toString();
    return api.get(`/students${qs ? `?${qs}` : ''}`);
  },
  getById: (id) => api.get(`/students/${id}`),
  create: (data) => api.post('/students', data),
  update: (id, data) => api.put(`/students/${id}`, data),
  delete: (id) => api.delete(`/students/${id}`),
  getStats: () => api.get('/students/stats'),
  getMajors: () => api.get('/students/majors'),
};
export default studentService;