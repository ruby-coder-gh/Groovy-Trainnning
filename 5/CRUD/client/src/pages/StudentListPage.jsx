import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Users, UserCheck, UserMinus, GraduationCap, AlertTriangle,
  Search, Edit3, Trash2, ChevronLeft, ChevronRight,
  ChevronUp, ChevronDown, ArrowUpDown, ExternalLink
} from 'lucide-react';
import { studentService } from '../services/studentService';

const STATUS_COLORS = { active: 'badge-active', inactive: 'badge-inactive', graduated: 'badge-graduated', suspended: 'badge-suspended' };

function StatCard({ icon: Icon, label, value, className, delay }) {
  return (
    <div className={`stat-card ${className} slide-up`} style={{ animationDelay: `${delay}ms` }}>
      <div className="stat-icon"><Icon size={20} /></div>
      <div className="stat-value">{value ?? '—'}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function ConfirmModal({ isOpen, title, message, onConfirm, onCancel, loading }) {
  if (!isOpen) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3><AlertTriangle size={20} style={{ color: 'var(--danger)' }} />{title}</h3>
        <p>{message}</p>
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
          <button className="btn btn-danger" onClick={onConfirm} disabled={loading}>{loading ? 'Deleting...' : 'Delete'}</button>
        </div>
      </div>
    </div>
  );
}

function StudentTable({ students, onDelete, sortBy, sortOrder, onSort }) {
  const navigate = useNavigate();
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try { await studentService.delete(deleteTarget.id); onDelete(deleteTarget.id); }
    catch (err) { alert(err.message); }
    finally { setDeleting(false); setDeleteTarget(null); }
  };

  const SortIcon = ({ col }) => {
    if (sortBy !== col) return <ArrowUpDown size={12} style={{ opacity: 0.3, marginLeft: 2 }} />;
    return sortOrder === 'ASC'
      ? <ChevronUp size={14} style={{ marginLeft: 2, color: 'var(--primary-600)' }} />
      : <ChevronDown size={14} style={{ marginLeft: 2, color: 'var(--primary-600)' }} />;
  };

  const handleSort = (col) => {
    if (sortBy === col) onSort(col, sortOrder === 'ASC' ? 'DESC' : 'ASC');
    else onSort(col, 'DESC');
  };

  if (!students || students.length === 0) {
    return (
      <div className="empty-state" style={{ padding: '3rem 2rem' }}>
        <div className="empty-icon"><Users size={28} /></div>
        <p>No students found</p>
        <p className="empty-sub">Try adjusting your search or filter</p>
      </div>
    );
  }

  return (
    <>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th className="sortable" onClick={() => handleSort('first_name')}>Student <SortIcon col="first_name" /></th>
              <th className="sortable" onClick={() => handleSort('email')}>Email <SortIcon col="email" /></th>
              <th>Major</th>
              <th className="sortable" onClick={() => handleSort('gpa')}>GPA <SortIcon col="gpa" /></th>
              <th className="sortable" onClick={() => handleSort('enrollment_date')}>Enrolled <SortIcon col="enrollment_date" /></th>
              <th className="sortable" onClick={() => handleSort('status')}>Status <SortIcon col="status" /></th>
              <th style={{ textAlign: 'right', width: 130 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id} onClick={() => navigate(`/students/${s.id}`)}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                    <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-full)', background: 'linear-gradient(135deg, var(--primary-100), var(--primary-200))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary-600)', fontWeight: 700, fontSize: '0.75rem', flexShrink: 0 }}>
                      {s.firstName[0]}{s.lastName[0]}
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--neutral-900)', fontSize: '0.875rem' }}>{s.firstName} {s.lastName}</div>
                  </div>
                </td>
                <td style={{ color: 'var(--neutral-500)' }}>{s.email}</td>
                <td>{s.major || <span style={{ color: 'var(--neutral-400)' }}>—</span>}</td>
                <td>{s.gpa !== null
                  ? <span style={{ fontWeight: 600, color: s.gpa >= 3.0 ? 'var(--success)' : s.gpa >= 2.0 ? 'var(--warning)' : 'var(--danger)' }}>{s.gpa.toFixed(2)}</span>
                  : <span style={{ color: 'var(--neutral-400)' }}>—</span>}
                </td>
                <td style={{ color: 'var(--neutral-500)' }}>{s.enrollmentDate ? new Date(s.enrollmentDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}</td>
                <td><span className={`badge ${STATUS_COLORS[s.status] || 'badge-active'}`}>{s.status}</span></td>
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'flex-end' }}>
                    <Link to={`/students/${s.id}/edit`} className="btn btn-ghost btn-sm btn-icon" onClick={(e) => e.stopPropagation()}><Edit3 size={15} /></Link>
                    <button className="btn btn-ghost btn-sm btn-icon" onClick={(e) => { e.stopPropagation(); setDeleteTarget(s); }} style={{ color: 'var(--danger)' }}><Trash2 size={15} /></button>
                    <Link to={`/students/${s.id}`} className="btn btn-ghost btn-sm btn-icon" onClick={(e) => e.stopPropagation()}><ExternalLink size={15} /></Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ConfirmModal isOpen={!!deleteTarget} title="Delete Student" message={deleteTarget ? `Delete "${deleteTarget.firstName} ${deleteTarget.lastName}"? This cannot be undone.` : ''} onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} loading={deleting} />
    </>
  );
}

function Pagination({ meta, onPageChange }) {
  if (!meta || meta.totalPages <= 1) return null;
  const { page, totalPages, total, hasNext, hasPrev } = meta;
  const pages = [];
  let start = Math.max(1, page - 2);
  let end = Math.min(totalPages, start + 4);
  if (end - start + 1 < 5) start = Math.max(1, end - 4);
  for (let i = start; i <= end; i++) pages.push(i);
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
      <div className="pagination-info"><span style={{ fontWeight: 600, color: 'var(--neutral-600)' }}>{total}</span> students · Page {page} of {totalPages}</div>
      <div className="pagination">
        <button disabled={!hasPrev} onClick={() => onPageChange(page - 1)}><ChevronLeft size={16} /></button>
        {pages.map(p => <button key={p} className={p === page ? 'active' : ''} onClick={() => onPageChange(p)}>{p}</button>)}
        <button disabled={!hasNext} onClick={() => onPageChange(page + 1)}><ChevronRight size={16} /></button>
      </div>
    </div>
  );
}

export default function StudentListPage() {
  const [students, setStudents] = useState([]);
  const [meta, setMeta] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('DESC');
  const [page, setPage] = useState(1);

  const fetchStudents = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await studentService.getAll({ page, limit: 10, search: search || undefined, status: statusFilter || undefined, sortBy, sortOrder });
      setStudents(r.data); setMeta(r.meta);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [page, search, statusFilter, sortBy, sortOrder]);

  const fetchStats = useCallback(async () => {
    try { const r = await studentService.getStats(); setStats(r.data); } catch {}
  }, []);

  useEffect(() => { fetchStudents(); }, [fetchStudents]);
  useEffect(() => { fetchStats(); }, [fetchStats]);
  useEffect(() => { setPage(1); }, [search, statusFilter]);

  const handleDelete = (id) => { setStudents(p => p.filter(s => s.id !== id)); fetchStats(); };

  return (
    <div>
      <div className="page-header"><h2><Users size={24} style={{ color: 'var(--primary-500)' }} /> Students</h2></div>
      {stats && <div className="stats-grid">
        <StatCard icon={Users} label="Total" value={stats.total} className="stat-total" delay={0} />
        <StatCard icon={UserCheck} label="Active" value={stats.active} className="stat-active" delay={50} />
        <StatCard icon={UserMinus} label="Inactive" value={stats.inactive} className="stat-inactive" delay={100} />
        <StatCard icon={GraduationCap} label="Graduated" value={stats.graduated} className="stat-graduated" delay={150} />
        <StatCard icon={AlertTriangle} label="Suspended" value={stats.suspended} className="stat-suspended" delay={200} />
      </div>}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-body" style={{ padding: '1rem 1.5rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
              <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--neutral-400)' }} />
              <input type="text" className="form-input" placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ paddingLeft: '2.25rem' }} />
            </div>
            <select className="form-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ maxWidth: 160 }}>
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="graduated">Graduated</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>
        </div>
      </div>
      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div className="loading-state"><div className="spinner" /><div className="loading-pulse"><span>Loading students</span></div></div>
        ) : error ? (
          <div className="card-body"><div className="alert alert-error">{error}</div></div>
        ) : (
          <>
            <StudentTable students={students} onDelete={handleDelete} sortBy={sortBy} sortOrder={sortOrder} onSort={(col, ord) => { setSortBy(col); setSortOrder(ord); }} />
            <div style={{ padding: '0.75rem 1.5rem 1rem', borderTop: '1px solid var(--neutral-100)' }}><Pagination meta={meta} onPageChange={setPage} /></div>
          </>
        )}
      </div>
    </div>
  );
}