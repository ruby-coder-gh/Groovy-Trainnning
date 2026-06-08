import pool from './database.js';

const sampleStudents = [
  { firstName: 'Alice', lastName: 'Johnson', email: 'alice.j@example.com', phone: '+1 (555) 111-1111', dateOfBirth: '2001-03-15', enrollmentDate: '2022-09-01', major: 'Computer Science', gpa: 3.85, status: 'active' },
  { firstName: 'Bob', lastName: 'Smith', email: 'bob.smith@example.com', phone: '+1 (555) 222-2222', dateOfBirth: '2000-07-22', enrollmentDate: '2022-09-01', major: 'Mathematics', gpa: 3.45, status: 'active' },
  { firstName: 'Carol', lastName: 'Williams', email: 'carol.w@example.com', phone: '+1 (555) 333-3333', dateOfBirth: '2002-01-10', enrollmentDate: '2023-01-15', major: 'Physics', gpa: 3.92, status: 'active' },
  { firstName: 'David', lastName: 'Brown', email: 'david.brown@example.com', phone: '+1 (555) 444-4444', dateOfBirth: '1999-11-05', enrollmentDate: '2021-09-01', major: 'Computer Science', gpa: 2.75, status: 'graduated' },
  { firstName: 'Eve', lastName: 'Davis', email: 'eve.davis@example.com', phone: '+1 (555) 555-5555', dateOfBirth: '2001-09-30', enrollmentDate: '2023-09-01', major: 'Biology', gpa: 3.60, status: 'active' },
  { firstName: 'Frank', lastName: 'Miller', email: 'frank.m@example.com', phone: '+1 (555) 666-6666', dateOfBirth: '2000-05-18', enrollmentDate: '2022-09-01', major: 'Computer Science', gpa: 2.10, status: 'suspended' },
  { firstName: 'Grace', lastName: 'Wilson', email: 'grace.w@example.com', phone: '+1 (555) 777-7777', dateOfBirth: '2002-12-25', enrollmentDate: '2024-01-15', major: 'Engineering', gpa: 3.75, status: 'active' },
  { firstName: 'Henry', lastName: 'Taylor', email: 'henry.t@example.com', phone: '+1 (555) 888-8888', dateOfBirth: '2001-08-14', enrollmentDate: '2023-09-01', major: 'History', gpa: 3.30, status: 'inactive' },
  { firstName: 'Ivy', lastName: 'Anderson', email: 'ivy.a@example.com', phone: '+1 (555) 999-9999', dateOfBirth: '2000-04-02', enrollmentDate: '2022-09-01', major: 'Mathematics', gpa: 3.98, status: 'active' },
  { firstName: 'Jack', lastName: 'Thomas', email: 'jack.t@example.com', phone: '+1 (555) 000-0000', dateOfBirth: '1998-06-20', enrollmentDate: '2020-09-01', major: 'Engineering', gpa: 3.15, status: 'graduated' },
  { firstName: 'Karen', lastName: 'Martinez', email: 'karen.m@example.com', phone: '+1 (555) 101-0101', dateOfBirth: '2002-02-28', enrollmentDate: '2024-09-01', major: 'Computer Science', gpa: 3.55, status: 'active' },
  { firstName: 'Leo', lastName: 'Garcia', email: 'leo.g@example.com', phone: '+1 (555) 202-0202', dateOfBirth: '2001-10-12', enrollmentDate: '2023-01-15', major: 'Physics', gpa: 2.90, status: 'active' },
];

async function seed() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('DELETE FROM students');
    for (const s of sampleStudents) {
      await client.query(
        `INSERT INTO students (first_name, last_name, email, phone, date_of_birth, enrollment_date, major, gpa, status) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
        [s.firstName, s.lastName, s.email, s.phone, s.dateOfBirth, s.enrollmentDate, s.major, s.gpa, s.status]
      );
    }
    await client.query('COMMIT');
    console.log(`Seeded ${sampleStudents.length} students!`);
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Seeding failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

seed().catch(console.error);