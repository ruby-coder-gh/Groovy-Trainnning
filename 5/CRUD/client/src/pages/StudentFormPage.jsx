import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Save, ArrowLeft, AlertCircle, Loader2 } from 'lucide-react';
import { studentService } from '../services/studentService';

const INIT = { firstName: '', lastName: '', email: '', phone: '', dateOfBirth: '', enrollmentDate: new Date().toISOString().split('T')[0], major: '', gpa: '', status: 'active' };
const STATUSES = ['active', 'inactive', 'graduated', 'suspended'];

export default function StudentFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form, setForm] = useState(INIT);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [submitError, setSubmitError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => { if (isEdit) loadStudent(); }, [id]);

  const loadStudent = async () => {
    setFetching(true);
    try {
      const r = await studentService.getById(id);
      const s = r.data;
      setForm({ firstName: s.firstName || '', lastName: s.lastName || '', email: s.email || '', phone: s.phone || '', dateOfBirth: s.dateOfBirth ? s.dateOfBirth.split('T')[0] : '', enrollmentDate: s.enrollmentDate ? s.enrollmentDate.split('T')[0] : '', major: s.major || '', gpa: s.gpa !== null ? String(s.gpa) : '', status: s.status || 'active' });
    } catch (err) { setSubmitError(err.message); }
    finally { setFetching(false); }
  };

  const validate = () => {
    const e = {};
    if (!form.firstName.trim()) e.firstName = 'First name is required';
    if (!form.lastName.trim()) e.lastName = 'Last name is required';
    if (!form.email.trim()) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Invalid email';
    if (form.phone && !/^[\d\s\-+()]{7,20}$/.test(form.phone)) e.phone = 'Invalid phone';
    if (form.gpa && (isNaN(form.gpa) || form.gpa < 0 || form.gpa > 4)) e.gpa = 'GPA must be 0–4';
    return e;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(p => ({ ...p, [name]: value }));
    if (errors[name]) setErrors(p => ({ ...p, [name]: undefined }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    setSuccess(null);
    const v = validate();
    if (Object.keys(v).length > 0) { setErrors(v); return; }
    const payload = { ...form, gpa: form.gpa ? parseFloat(form.gpa) : null, dateOfBirth: form.dateOfBirth || null };
    setLoading(true);
    try {
      if (isEdit) { await studentService.update(id, payload); setSuccess('Updated! Redirecting...'); }
      else { await studentService.create(payload); setSuccess('Created! Redirecting...'); }
      setTimeout(() => navigate('/'), 1000);
    } catch (err) {
      setSubmitError(err.message);
      if (err.details) {
        const fe = {};
        err.details.forEach(d => {
          const m = Object.keys(payload).find(k => k.toLowerCase() === d.field.toLowerCase() || d.field.includes(k.toLowerCase()));
          if (m) fe[m] = d.message;
        });
        setErrors(fe);
      }
    } finally { setLoading(false); }
  };

  if (fetching) {
    return <div className="loading-state"><div className="spinner" /><div className="loading-pulse"><span>Loading student data</span></div></div>;
  }

  return (
    <div className="card" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div className="card-header">
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><User size={22} style={{ color: 'var(--primary-500)' }} /> {isEdit ? 'Edit Student' : 'Add New Student'}</h2>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="card-body">
          {submitError && <div className="alert alert-error mb-4"><AlertCircle size={16} />{submitError}</div>}
          {success && <div className="alert alert-success mb-4">{success}</div>}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">First Name *</label>
              <input name="firstName" className={`form-input ${errors.firstName ? 'error' : ''}`} value={form.firstName} onChange={handleChange} placeholder="John" />
              {errors.firstName && <div className="form-error"><AlertCircle size={12} />{errors.firstName}</div>}
            </div>
            <div className="form-group">
              <label className="form-label">Last Name *</label>
              <input name="lastName" className={`form-input ${errors.lastName ? 'error' : ''}`} value={form.lastName} onChange={handleChange} placeholder="Doe" />
              {errors.lastName && <div className="form-error"><AlertCircle size={12} />{errors.lastName}</div>}
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Email *</label>
            <input name="email" type="email" className={`form-input ${errors.email ? 'error' : ''}`} value={form.email} onChange={handleChange} placeholder="john@example.com" />
            {errors.email && <div className="form-error"><AlertCircle size={12} />{errors.email}</div>}
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input name="phone" className={`form-input ${errors.phone ? 'error' : ''}`} value={form.phone} onChange={handleChange} placeholder="+1 (555) 123-4567" />
              {errors.phone && <div className="form-error"><AlertCircle size={12} />{errors.phone}</div>}
            </div>
            <div className="form-group">
              <label className="form-label">Major</label>
              <input name="major" className={`form-input ${errors.major ? 'error' : ''}`} value={form.major} onChange={handleChange} placeholder="Computer Science" />
              {errors.major && <div className="form-error"><AlertCircle size={12} />{errors.major}</div>}
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Date of Birth</label>
              <input name="dateOfBirth" type="date" className="form-input" value={form.dateOfBirth} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Enrollment Date</label>
              <input name="enrollmentDate" type="date" className="form-input" value={form.enrollmentDate} onChange={handleChange} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">GPA (0–4)</label>
              <input name="gpa" type="number" step="0.01" min="0" max="4" className={`form-input ${errors.gpa ? 'error' : ''}`} value={form.gpa} onChange={handleChange} placeholder="3.50" />
              {errors.gpa && <div className="form-error"><AlertCircle size={12} />{errors.gpa}</div>}
            </div>
            <div className="form-group">
              <label className="form-label">Status</label>
              <select name="status" className="form-select" value={form.status} onChange={handleChange}>
                {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
          </div>
        </div>
        <div className="card-footer" style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}><ArrowLeft size={16} /> Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <><Loader2 size={16} style={{ animation: 'spin 0.6s linear infinite' }} /> Saving...</> : <><Save size={16} /> {isEdit ? 'Update' : 'Create'}</>}
          </button>
        </div>
      </form>
    </div>
  );
}