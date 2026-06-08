import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Users, Plus, ArrowLeft } from 'lucide-react';

export default function Layout({ children }) {
  const isList = useLocation().pathname === '/';
  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/" className="logo">
          <div className="logo-icon"><Users size={18} /></div>
          <span className="logo-text">StudentHub</span>
        </Link>
        <div className="header-actions">
          {!isList ? (
            <Link to="/" className="btn btn-ghost btn-sm"><ArrowLeft size={16} /> Back</Link>
          ) : (
            <Link to="/students/new" className="btn btn-primary btn-sm"><Plus size={16} /> Add Student</Link>
          )}
        </div>
      </header>
      <main className="app-main fade-in">{children}</main>
    </div>
  );
}