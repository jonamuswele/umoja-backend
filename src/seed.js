import { getDb } from './db.js';

async function seed() {
  console.log("🌱 Seeding Umoja Terra Database (Clean Slate)...");
  const db = getDb();

  // Clear existing data
  await db.execute('DELETE FROM plot_views');
  await db.execute('DELETE FROM inquiries');
  await db.execute('DELETE FROM plots');
  await db.execute('DELETE FROM countries');
  await db.execute('DELETE FROM notifications');
  await db.execute('DELETE FROM users');

  // Insert default pre-approved admin
  await db.execute(`
    INSERT INTO users (username, password_hash, role, is_approved, is_suspended)
    VALUES (?, ?, ?, ?, ?)
  `, ['admin', 'admin', 'admin', 1, 0]);

  console.log("✅ Database successfully reset with one pre-approved 'admin' user!");
}

seed().catch(console.error);
