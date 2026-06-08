import { query } from '../config/database.js';

export class Student {
  constructor(data) {
    this.id = data.id;
    this.firstName = data.first_name;
    this.lastName = data.last_name;
    this.email = data.email;
    this.phone = data.phone;
    this.dateOfBirth = data.date_of_birth;
    this.enrollmentDate = data.enrollment_date;
    this.major = data.major;
    this.gpa = data.gpa ? parseFloat(data.gpa) : null;
    this.status = data.status;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
  }

  static fromRow(row) { return new Student(row); }

  static async findAll({ page = 1, limit = 10, search, status, major, sortBy = 'created_at', sortOrder = 'DESC' } = {}) {
    const offset = (page - 1) * limit;
    const conditions = [];
    const params = [];
    let pi = 1;

    if (search) {
      conditions.push(`(first_name ILIKE $${pi} OR last_name ILIKE $${pi} OR email ILIKE $${pi})`);
      params.push(`%${search}%`);
      pi++;
    }
    if (status) { conditions.push(`status = $${pi}`); params.push(status); pi++; }
    if (major) { conditions.push(`major = $${pi}`); params.push(major); pi++; }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const safeCols = ['first_name', 'last_name', 'email', 'enrollment_date', 'gpa', 'created_at', 'updated_at', 'status'];
    const safeOrder = ['ASC', 'DESC'];
    const col = safeCols.includes(sortBy) ? sortBy : 'created_at';
    const ord = safeOrder.includes(sortOrder.toUpperCase()) ? sortOrder.toUpperCase() : 'DESC';

    params.push(limit, offset);
    const [countRes, dataRes] = await Promise.all([
      query(`SELECT COUNT(*) FROM students ${where}`, params.slice(0, -2)),
      query(`SELECT * FROM students ${where} ORDER BY ${col} ${ord} LIMIT $${pi} OFFSET $${pi + 1}`, params)
    ]);

    const total = parseInt(countRes.rows[0].count);
    return {
      data: dataRes.rows.map(Student.fromRow),
      meta: { page, limit, total, totalPages: Math.ceil(total / limit), hasNext: page < Math.ceil(total / limit), hasPrev: page > 1 }
    };
  }

  static async findById(id) {
    const res = await query('SELECT * FROM students WHERE id = $1', [id]);
    return res.rows[0] ? Student.fromRow(res.rows[0]) : null;
  }

  static async findByEmail(email) {
    const res = await query('SELECT * FROM students WHERE email = $1', [email]);
    return res.rows[0] ? Student.fromRow(res.rows[0]) : null;
  }

  static async create(d) {
    const res = await query(
      `INSERT INTO students (first_name, last_name, email, phone, date_of_birth, enrollment_date, major, gpa, status)
       VALUES ($1,$2,$3,$4,$5,COALESCE($6, CURRENT_DATE),$7,$8,$9) RETURNING *`,
      [d.firstName, d.lastName, d.email, d.phone, d.dateOfBirth, d.enrollmentDate, d.major, d.gpa, d.status || 'active']
    );
    return Student.fromRow(res.rows[0]);
  }

  static async update(id, d) {
    const fields = [];
    const vals = [];
    let pi = 1;
    const map = { firstName: 'first_name', lastName: 'last_name', email: 'email', phone: 'phone', dateOfBirth: 'date_of_birth', enrollmentDate: 'enrollment_date', major: 'major', gpa: 'gpa', status: 'status' };
    for (const [key, col] of Object.entries(map)) {
      if (d[key] !== undefined) { fields.push(`${col} = $${pi}`); vals.push(d[key]); pi++; }
    }
    if (fields.length === 0) throw new Error('No valid fields');
    vals.push(id);
    const res = await query(`UPDATE students SET ${fields.join(', ')} WHERE id = $${pi} RETURNING *`, vals);
    return res.rows[0] ? Student.fromRow(res.rows[0]) : null;
  }

  static async delete(id) {
    const res = await query('DELETE FROM students WHERE id = $1 RETURNING *', [id]);
    return res.rows[0] ? Student.fromRow(res.rows[0]) : null;
  }

  static async getMajors() {
    const res = await query('SELECT DISTINCT major FROM students WHERE major IS NOT NULL ORDER BY major');
    return res.rows.map(r => r.major);
  }

  static async getStats() {
    const res = await query(`
      SELECT COUNT(*) as total,
        COUNT(*) FILTER (WHERE status='active') as active,
        COUNT(*) FILTER (WHERE status='inactive') as inactive,
        COUNT(*) FILTER (WHERE status='graduated') as graduated,
        COUNT(*) FILTER (WHERE status='suspended') as suspended,
        AVG(gpa) as avg_gpa FROM students
    `);
    const r = res.rows[0];
    return { total: parseInt(r.total), active: parseInt(r.active), inactive: parseInt(r.inactive), graduated: parseInt(r.graduated), suspended: parseInt(r.suspended), avgGpa: r.avg_gpa ? parseFloat(r.avg_gpa).toFixed(2) : null };
  }
}
export default Student;