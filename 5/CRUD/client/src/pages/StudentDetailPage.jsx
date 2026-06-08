import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  User, Mail, Phone, Calendar, BookOpen, TrendingUp, Shield,
  Edit3, Trash2, ArrowLeft, Clock, Fingerprint, GraduationCap, AlertTriangle
} from 'lucide-react';
import { studentService } from '../services/studentService';

const STATUS_CONFIG = {
  active: { class: 'badge-active', icon: Shield, gradient: 'linear-gradient(135deg, #10b981, #059669)' },
  inactive: { class: 'badge-inactive', icon: Shield, gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  graduated: { class: 'badge-graduated', icon: GraduationCap, gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)' },
  suspended: { class: 'badge-suspended', icon: AlertTriangle, gradient: 'linear-gradient(135deg, #ef4444, #dc2626)' },
};

function DetailItem({ label, value, icon: Icon }) {
  return (
    <div className="detail-item">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.125rem' }}>
        {Icon && <Icon size={12} style={{ color: 'var(--neutral-400)' }} />}
        <div className="detail-label">{label}</div>
      </div>
      <div className="detail-value">{value ?? <span style={{ color: 'var(--neutral-300)' }}>—</span>}</div>
    </div>
  );
}

function DetailSection({ title, children }) {
  return <div><div className="detail-section-title">{title}</div>{children}</div>;
}

export default function StudentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  useEffect(() => { loadStudent(); }, [id]);

  const loadStudent = async () => {
    setLoading(true); setError(null);
    try { const r = await studentService.getById(id); setStudent(r.data); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try { await studentService.delete(id); navigate('/'); }
    catch (err) { alert(err.message); setDeleting(false); setShowDelete(false); }
  };

  if (loading) {
    return <div className="loading-state"><div className="spinner" /><div className="loading-pulse"><span>Loading student details</span></div></div>;
  }

  if (error) {
    return (
      <div className="card" style={{ maxWidth: '600px', margin: '2rem auto' }}>
        <div className="card-body" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ width: 56, height: 56, borderRadius: 'var(--radius-full)', background: 'var(--danger-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}><AlertTriangle size={28} style={{ color: 'var(--danger)' }} /></div>
          <h3 style={{ marginBottom: '0.5rem' }}>Not Found</h3>
          <p style={{ color: 'var(--neutral-500)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>{error}</p>
          <Link to="/" className="btn btn-primary"><ArrowLeft size={16} /> Back</Link>
        </div>
      </div>
    );
  }

  if (!student) return null;

  const cfg = STATUS_CONFIG[student.status] || STATUS_CONFIG.active;
  const initials = `${student.firstName[0]}${student.lastName[0]}`;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {showDelete && (
        <div className="modal-overlay" onClick={() => setShowDelete(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3><AlertTriangle size={20} style={{ color: 'var(--danger)' }} /> Delete Student</h3>
            <p>Delete <strong>{student.firstName} {student.lastName}</strong>? This cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowDelete(false)} disabled={deleting}>Cancel</button>
              <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>{deleting ? 'Deleting...' : 'Delete'}</button>
            </div>
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1.5rem', overflow: 'hidden' }}>
        <div style={{ background: cfg.gradient, padding: '2rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ width: 72, height: 72, borderRadius: 'var(--radius-full)', background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 800, fontSize: '1.5rem', border: '2px solid rgba(255,255,255,0.3)', flexShrink: 0 }}>
            {initials}
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={{ color: 'white', margin: 0, fontSize: '1.5rem' }}>{student.firstName} {student.lastName}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.375rem' }}>
              <span className={`badge ${cfg.class}`} style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}><Shield size={12} />{student.status}</span>
              {student.major && <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.8125rem' }}>{student.major}</span>}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link to={`/students/${student.id}/edit`} className="btn" style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)', backdropFilter: 'blur(8px)' }}><Edit3 size={15} /> Edit</Link>
            <button className="btn" style={{ background: 'rgba(255,255,255,0.15)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', backdropFilter: 'blur(8px)' }} onClick={() => setShowDelete(true)}><Trash2 size={15} /> Delete</button>
          </div>
        </div>
        <div className="card-body">
          <div className="detail-grid">
            <DetailSection title="Contact">
              <DetailItem label="Email" value={student.email} icon={Mail} />
              <DetailItem label="Phone" value={student.phone} icon={Phone} />
            </DetailSection>
            <DetailSection title="Academic">
              <DetailItem label="Major" value={student.major} icon={BookOpen} />
              <DetailItem label="GPA" value={student.gpa !== null ? student.gpa.toFixed(2) : null} icon={TrendingUp} />
              <DetailItem label="Enrolled" value={student.enrollmentDate ? new Date(student.enrollmentDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null} icon={Calendar} />
            </DetailSection>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Fingerprint size={18} style={{ color: 'var(--primary-500)' }} /> Additional Info</h3></div>
        <div className="card-body">
          <div className="detail-grid">
            <DetailSection title="Personal">
              <DetailItem label="DOB" value={student.dateOfBirth ? new Date(student.dateOfBirth).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null} icon={Calendar} />
              <DetailItem label="Student ID" value={student.id} icon={Fingerprint} />
            </DetailSection>
            <DetailSection title="System">
              <DetailItem label="Created" value={student.createdAt ? new Date(student.createdAt).toLocaleString() : null} icon={Clock} />
              <DetailItem label="Updated" value={student.updatedAt ? new Date(student.updatedAt).toLocaleString() : null} icon={Clock} />
            </DetailSection>
          </div>
        </div>
        <div className="card-footer" style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Link to="/" className="btn btn-ghost"><ArrowLeft size={16} /> Back</Link>
          <Link to={`/students/${student.id}/edit`} className="btn btn-primary"><Edit3 size={16} /> Edit</Link>
        </div>
      </div>
    </div>
  );
}