const { Pool } = require('pg');

const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'ats_db',
  password: process.env.DB_PASSWORD || 'root',
  port: parseInt(process.env.DB_PORT || '5432', 10),
});

async function migrate() {
  try {
    await pool.query(`
      ALTER TABLE public.users 
      ADD COLUMN IF NOT EXISTS reset_token TEXT,
      ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ;
    `);
    console.log('Migration successful: Added reset_token and reset_token_expires to users table.');
  } catch (e) {
    console.error('Migration failed:', e);
  } finally {
    await pool.end();
  }
}

migrate();
