import Student from '../models/Student.js';
import { AppError } from '../utils/AppError.js';

export const studentController = {
  async getAll(req, res, next) {
    try {
      const { page, limit, search, status, major, sortBy, sortOrder } = req.query;
      const result = await Student.findAll({ page: parseInt(page) || 1, limit: Math.min(parseInt(limit) || 10, 100), search, status, major, sortBy, sortOrder });
      res.json({ success: true, data: result.data, meta: result.meta });
    } catch (error) { next(error); }
  },

  async getById(req, res, next) {
    try {
      const student = await Student.findById(req.params.id);
      if (!student) throw new AppError('Student not found', 404, 'STUDENT_NOT_FOUND');
      res.json({ success: true, data: student });
    } catch (error) { next(error); }
  },

  async create(req, res, next) {
    try {
      const existing = await Student.findByEmail(req.body.email);
      if (existing) throw new AppError('Student with this email already exists', 409, 'EMAIL_EXISTS');
      const student = await Student.create(req.body);
      res.status(201).json({ success: true, data: student, message: 'Student created successfully' });
    } catch (error) { next(error); }
  },

  async update(req, res, next) {
    try {
      if (req.body.email) {
        const existing = await Student.findByEmail(req.body.email);
        if (existing && existing.id !== req.params.id) throw new AppError('Student with this email already exists', 409, 'EMAIL_EXISTS');
      }
      const student = await Student.update(req.params.id, req.body);
      if (!student) throw new AppError('Student not found', 404, 'STUDENT_NOT_FOUND');
      res.json({ success: true, data: student, message: 'Student updated successfully' });
    } catch (error) { next(error); }
  },

  async delete(req, res, next) {
    try {
      const student = await Student.delete(req.params.id);
      if (!student) throw new AppError('Student not found', 404, 'STUDENT_NOT_FOUND');
      res.json({ success: true, message: 'Student deleted successfully' });
    } catch (error) { next(error); }
  },

  async getMajors(req, res, next) {
    try { const majors = await Student.getMajors(); res.json({ success: true, data: majors }); }
    catch (error) { next(error); }
  },

  async getStats(req, res, next) {
    try { const stats = await Student.getStats(); res.json({ success: true, data: stats }); }
    catch (error) { next(error); }
  }
};
export default studentController;