import pool from './database.js';

const createStudentsTable = `
  CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    major VARCHAR(100),
    gpa DECIMAL(3,2) CHECK (gpa >= 0.00 AND gpa <= 4.00),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
  );
`;

const createIndexes = `
  CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
  CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
  CREATE INDEX IF NOT EXISTS idx_students_major ON students(major);
`;

const createTriggerFn = `
  CREATE OR REPLACE FUNCTION update_updated_at_column()
  RETURNS TRIGGER AS $$
  BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
  $$ language 'plpgsql';
`;

const createTrigger = `
  DROP TRIGGER IF EXISTS update_students_updated_at ON students;
  CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
`;

async function migrate() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query(createStudentsTable);
    await client.query(createIndexes);
    await client.query(createTriggerFn);
    await client.query(createTrigger);
    await client.query('COMMIT');
    console.log('Migration completed successfully!');
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Migration failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

migrate().catch(console.error);