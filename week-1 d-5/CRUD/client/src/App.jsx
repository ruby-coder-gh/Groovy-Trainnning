import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import StudentListPage from './pages/StudentListPage';
import StudentFormPage from './pages/StudentFormPage';
import StudentDetailPage from './pages/StudentDetailPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<StudentListPage />} />
        <Route path="/students/new" element={<StudentFormPage />} />
        <Route path="/students/:id/edit" element={<StudentFormPage />} />
        <Route path="/students/:id" element={<StudentDetailPage />} />
      </Routes>
    </Layout>
  );
}