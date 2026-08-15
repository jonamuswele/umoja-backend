import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { getDb } from './db.js';
import { 
  AFRICAN_FLAGS, 
  serializePlot, 
  serializeCountry, 
  serializeInquiry 
} from './serializers.js';

const app = new Hono();

// Global CORS Middleware
app.use('/*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'X-User-Username', 'X-User-Role', 'Authorization'],
  exposeHeaders: ['Content-Length'],
  maxAge: 600,
}));

// Root check
app.get('/', (c) => {
  return c.json({ status: 'online', service: 'Umoja Terra Hono API (Edge-Ready)' });
});

// ==========================================
// 1. AUTHENTICATION & REGISTRATION
// ==========================================

// Register Landowner
app.post('/api/auth/register', async (c) => {
  const db = getDb(c.env);
  const body = await c.req.json().catch(() => ({}));
  const username = (body.username || '').trim().toLowerCase();
  const password = body.password || '';
  const label = (body.label || username).trim();

  if (username.length < 3) {
    return c.json({ detail: 'Username must be at least 3 characters' }, 400);
  }

  const existing = await db.queryFirst('SELECT * FROM users WHERE username = ?', [username]);
  if (existing) {
    return c.json({ detail: 'Username is already taken' }, 400);
  }

  await db.execute(
    'INSERT INTO users (username, password_hash, role, is_approved, is_suspended) VALUES (?, ?, ?, ?, ?)',
    [username, password, 'owner', 0, 0]
  );

  // Dispatch Admin Notification
  const notifId = `notif-reg-${username}-${Date.now()}`;
  await db.execute(
    'INSERT INTO notifications (id, message, read, timestamp) VALUES (?, ?, ?, ?)',
    [notifId, `New registration request: '${username}' (${label}) is awaiting approval.`, 0, new Date().toISOString()]
  );

  return c.json({
    username,
    role: 'owner',
    label,
    is_approved: false,
    is_suspended: false
  });
});

// Login
app.post('/api/auth/login', async (c) => {
  const db = getDb(c.env);
  const body = await c.req.json().catch(() => ({}));
  const username = (body.username || '').trim().toLowerCase();
  const password = body.password || '';

  const user = await db.queryFirst('SELECT * FROM users WHERE username = ?', [username]);
  if (!user) {
    return c.json({ detail: 'Incorrect credentials. Please register first.' }, 400);
  }

  if (user.password_hash !== password) {
    return c.json({ detail: 'Incorrect password' }, 400);
  }

  if (Boolean(user.is_suspended)) {
    return c.json({ detail: 'Your account has been suspended by the administrator. Please contact support.' }, 403);
  }

  if (!Boolean(user.is_approved)) {
    return c.json({ detail: 'Your landowner account is pending administrator approval.' }, 403);
  }

  return c.json({
    username: user.username,
    role: user.role,
    label: user.username,
    is_approved: Boolean(user.is_approved),
    is_suspended: Boolean(user.is_suspended)
  });
});

// ==========================================
// 2. COUNTRIES & DIRECTORY
// ==========================================

// Get Directory (Public + Admin Filtering)
app.get('/api/countries', async (c) => {
  const db = getDb(c.env);
  const userRole = c.req.header('x-user-role') || '';
  const userUsername = c.req.header('x-user-username') || '';

  const countries = await db.query('SELECT * FROM countries');
  const allPlots = await db.query('SELECT * FROM plots');

  // Group plots by country_id
  const plotsByCountry = {};
  for (const p of allPlots) {
    if (!plotsByCountry[p.country_id]) plotsByCountry[p.country_id] = [];
    plotsByCountry[p.country_id].push(p);
  }

  if (userRole === 'admin') {
    return c.json(countries.map(country => serializeCountry(country, plotsByCountry[country.id] || [])));
  }

  const result = [];
  for (const country of countries) {
    if (!Boolean(country.is_visible)) continue;

    const countryPlots = plotsByCountry[country.id] || [];
    const visiblePlots = countryPlots.filter(p => {
      return Boolean(p.is_visible) || (userUsername && p.owner_username === userUsername);
    });

    result.push(serializeCountry(country, visiblePlots));
  }

  return c.json(result);
});

// Create Country (Admin Only)
app.post('/api/countries', async (c) => {
  const db = getDb(c.env);
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') {
    return c.json({ detail: 'Only the main admin can add new countries' }, 403);
  }

  const body = await c.req.json().catch(() => ({}));
  const name = (body.name || '').trim();
  if (!name) return c.json({ detail: 'Country name is required' }, 400);

  const countryId = name.toLowerCase().replace(/\s+/g, '-');
  const existing = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countryId]);
  if (existing) return c.json({ detail: 'Country already exists' }, 400);

  const flag = AFRICAN_FLAGS[countryId] || (body.flag || '').trim() || '🌍';
  const defaultDesc = `Welcome to ${name}. Explore vetted, high-value investment plots across premium zones in this growing region.`;

  await db.execute(`
    INSERT INTO countries (
      id, name, flag, motto, accent, desc, video_url, highlights, potential_neighborhoods, culture_info, is_visible
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [
    countryId,
    name,
    flag,
    'A Vibrant New Region',
    '#1A3E26',
    defaultDesc,
    'https://www.w3schools.com/html/mov_bbb.mp4',
    JSON.stringify(['Secure Ownership', 'Vetted Surveyor Beacons', 'Gated Access']),
    JSON.stringify([]),
    JSON.stringify({
      whyLive: `Live here to participate in ${name}'s rising market and beautiful community landscape.`,
      bestBuild: 'Modern Eco-Villas or architectural designs matching the local topography.',
      culture: 'Warm hospitality, rich regional traditions, and community values.',
      culturePhotos: []
    }),
    1
  ]);

  const created = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countryId]);
  return c.json(serializeCountry(created, []));
});

// Update Country Specifications (Admin Only)
app.put('/api/countries/:country_id', async (c) => {
  const db = getDb(c.env);
  const countryId = c.req.param('country_id');
  const userRole = c.req.header('x-user-role') || '';

  if (userRole !== 'admin') {
    return c.json({ detail: 'Only the main admin can customize country landing pages' }, 403);
  }

  const country = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countryId]);
  if (!country) return c.json({ detail: 'Country not found' }, 404);

  const body = await c.req.json().catch(() => ({}));

  await db.execute(`
    UPDATE countries SET
      motto = ?,
      desc = ?,
      video_url = ?,
      accent = ?,
      flag = ?,
      highlights = ?,
      potential_neighborhoods = ?,
      culture_info = ?
    WHERE id = ?
  `, [
    body.motto ?? country.motto,
    body.desc ?? country.desc,
    body.videoUrl ?? country.video_url,
    body.accent ?? country.accent,
    body.flag ?? country.flag,
    JSON.stringify(body.highlights || []),
    JSON.stringify(body.potentialNeighborhoods || []),
    JSON.stringify(body.cultureInfo || {}),
    countryId
  ]);

  const updated = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countryId]);
  const plots = await db.query('SELECT * FROM plots WHERE country_id = ?', [countryId]);
  return c.json(serializeCountry(updated, plots));
});

// Toggle Country Visibility (Admin Only)
app.post('/api/admin/countries/:country_id/visibility', async (c) => {
  const db = getDb(c.env);
  const countryId = c.req.param('country_id');
  const userRole = c.req.header('x-user-role') || '';

  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const country = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countryId]);
  if (!country) return c.json({ detail: 'Country not found' }, 404);

  const nextVisible = country.is_visible ? 0 : 1;
  await db.execute('UPDATE countries SET is_visible = ? WHERE id = ?', [nextVisible, countryId]);

  return c.json({ status: 'success', isVisible: Boolean(nextVisible) });
});

// ==========================================
// 3. PLOTS MANAGEMENT
// ==========================================

// Create Plot
app.post('/api/plots', async (c) => {
  const db = getDb(c.env);
  const userUsername = c.req.header('x-user-username') || '';
  const userRole = c.req.header('x-user-role') || '';

  if (!['admin', 'owner'].includes(userRole)) {
    return c.json({ detail: 'Insufficient permissions' }, 403);
  }

  const body = await c.req.json().catch(() => ({}));
  const countryNameRaw = (body.country_id || '').trim();
  if (!countryNameRaw) return c.json({ detail: 'Country name cannot be empty' }, 400);

  const countrySlug = countryNameRaw.toLowerCase().replace(/\s+/g, '-');
  let country = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [countrySlug]);

  if (!country) {
    const flagEmoji = AFRICAN_FLAGS[countrySlug] || '🌍';
    await db.execute(`
      INSERT INTO countries (
        id, name, flag, motto, accent, desc, video_url, highlights, potential_neighborhoods, culture_info, is_visible
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      countrySlug,
      countryNameRaw,
      flagEmoji,
      'A Vibrant New Region',
      '#1A3E26',
      `Welcome to ${countryNameRaw}. Explore vetted, high-value investment plots across premium zones in this growing region.`,
      'https://www.w3schools.com/html/mov_bbb.mp4',
      JSON.stringify(['Secure Ownership', 'Vetted Surveyor Beacons', 'Gated Access']),
      JSON.stringify([]),
      JSON.stringify({
        whyLive: `Live here to participate in ${countryNameRaw}'s rising market and beautiful community landscape.`,
        bestBuild: 'Modern Eco-Villas or architectural designs matching the local topography.',
        culture: 'Warm hospitality, rich regional traditions, and community values.',
        culturePhotos: []
      }),
      1
    ]);

    // Notify Admin
    const notifId = `notif-country-${countrySlug}-${Date.now()}`;
    await db.execute(
      'INSERT INTO notifications (id, message, read, timestamp) VALUES (?, ?, ?, ?)',
      [notifId, `Landowner added listings in '${countryNameRaw}'. Landing page needs customization.`, 0, new Date().toISOString()]
    );
  }

  const plotId = `plot-${Date.now()}`;
  await db.execute(`
    INSERT INTO plots (
      id, title, size, price, neighborhood, owner_username, country_id, photos, is_visible
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [
    plotId,
    body.title,
    body.size,
    Number(body.price),
    body.neighborhood,
    userUsername,
    countrySlug,
    JSON.stringify(body.photos || []),
    1
  ]);

  const created = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  return c.json(serializePlot(created));
});

// Update Plot
app.put('/api/plots/:plot_id', async (c) => {
  const db = getDb(c.env);
  const plotId = c.req.param('plot_id');
  const userUsername = c.req.header('x-user-username') || '';
  const userRole = c.req.header('x-user-role') || '';

  const plot = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  if (!plot) return c.json({ detail: 'Plot not found' }, 404);

  if (userRole !== 'admin' && plot.owner_username !== userUsername) {
    return c.json({ detail: 'You do not own this listing' }, 403);
  }

  const body = await c.req.json().catch(() => ({}));
  await db.execute(`
    UPDATE plots SET
      title = ?,
      size = ?,
      price = ?,
      neighborhood = ?,
      photos = ?
    WHERE id = ?
  `, [
    body.title ?? plot.title,
    body.size ?? plot.size,
    Number(body.price ?? plot.price),
    body.neighborhood ?? plot.neighborhood,
    JSON.stringify(body.photos || []),
    plotId
  ]);

  const updated = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  return c.json(serializePlot(updated));
});

// Delete Plot
app.delete('/api/plots/:plot_id', async (c) => {
  const db = getDb(c.env);
  const plotId = c.req.param('plot_id');
  const userUsername = c.req.header('x-user-username') || '';
  const userRole = c.req.header('x-user-role') || '';

  const plot = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  if (!plot) return c.json({ detail: 'Plot not found' }, 404);

  if (userRole !== 'admin' && plot.owner_username !== userUsername) {
    return c.json({ detail: 'You do not own this listing' }, 403);
  }

  await db.execute('DELETE FROM inquiries WHERE plot_id = ?', [plotId]);
  await db.execute('DELETE FROM plot_views WHERE plot_id = ?', [plotId]);
  await db.execute('DELETE FROM plots WHERE id = ?', [plotId]);

  return c.json({ status: 'success', message: `Plot ${plotId} successfully deleted.` });
});

// Toggle Plot Visibility (Admin Only)
app.post('/api/admin/plots/:plot_id/visibility', async (c) => {
  const db = getDb(c.env);
  const plotId = c.req.param('plot_id');
  const userRole = c.req.header('x-user-role') || '';

  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const plot = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  if (!plot) return c.json({ detail: 'Plot not found' }, 404);

  const nextVisible = plot.is_visible ? 0 : 1;
  await db.execute('UPDATE plots SET is_visible = ? WHERE id = ?', [nextVisible, plotId]);

  return c.json({ status: 'success', isVisible: Boolean(nextVisible) });
});

// Track View
app.post('/api/plots/:plot_id/view', async (c) => {
  const db = getDb(c.env);
  const plotId = c.req.param('plot_id');

  const plot = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [plotId]);
  if (!plot) return c.json({ detail: 'Plot not found' }, 404);

  await db.execute('INSERT INTO plot_views (plot_id, timestamp) VALUES (?, ?)', [plotId, new Date().toISOString()]);
  return c.json({ status: 'success' });
});

// ==========================================
// 4. INQUIRIES & DASHBOARD ANALYTICS
// ==========================================

// Create Inquiry
app.post('/api/inquiries', async (c) => {
  const db = getDb(c.env);
  const body = await c.req.json().catch(() => ({}));

  const plot = await db.queryFirst('SELECT * FROM plots WHERE id = ?', [body.plot_id]);
  if (!plot) return c.json({ detail: 'Plot not found' }, 404);

  const inqId = `inq-${Date.now()}`;
  const timestamp = new Date().toISOString();

  await db.execute(`
    INSERT INTO inquiries (
      id, plot_id, full_name, email, phone, current_city, message, type, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [
    inqId,
    body.plot_id,
    body.fullName,
    body.email,
    body.phone || '',
    body.currentCity || '',
    body.message,
    body.type,
    timestamp
  ]);

  const created = await db.queryFirst('SELECT * FROM inquiries WHERE id = ?', [inqId]);
  const country = await db.queryFirst('SELECT * FROM countries WHERE id = ?', [plot.country_id]);

  return c.json(serializeInquiry(created, plot.title, country ? country.name : 'Unknown'));
});

// Get Inquiries / Leads
app.get('/api/inquiries', async (c) => {
  const db = getDb(c.env);
  const userUsername = c.req.header('x-user-username') || '';
  const userRole = c.req.header('x-user-role') || '';

  let sql = `
    SELECT i.*, p.title as plot_title, c.name as country_name
    FROM inquiries i
    JOIN plots p ON i.plot_id = p.id
    JOIN countries c ON p.country_id = c.id
  `;
  const params = [];

  if (userRole !== 'admin') {
    sql += ' WHERE p.owner_username = ?';
    params.push(userUsername);
  }
  sql += ' ORDER BY i.timestamp DESC';

  const rows = await db.query(sql, params);
  return c.json(rows.map(row => serializeInquiry(row, row.plot_title, row.country_name)));
});

// Dashboard Stats & 7-Day Clicks Chart
app.get('/api/stats/dashboard', async (c) => {
  const db = getDb(c.env);
  const userUsername = c.req.header('x-user-username') || '';
  const userRole = c.req.header('x-user-role') || '';

  let userPlots = [];
  if (userRole === 'admin') {
    userPlots = await db.query('SELECT id FROM plots');
  } else {
    userPlots = await db.query('SELECT id FROM plots WHERE owner_username = ?', [userUsername]);
  }

  const plotIds = userPlots.map(p => p.id);
  if (plotIds.length === 0) {
    return c.json({
      totalViews: 0,
      totalInquiries: 0,
      conversionRate: '0.0',
      leads: [],
      viewsChart: Array.from({ length: 7 }).map((_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - (6 - i));
        return {
          day: d.toLocaleDateString('en-US', { weekday: 'short' }),
          count: 0,
          active: i === 6
        };
      })
    });
  }

  const placeholders = plotIds.map(() => '?').join(',');

  // Views count
  const viewsRes = await db.queryFirst(
    `SELECT COUNT(*) as count FROM plot_views WHERE plot_id IN (${placeholders})`,
    plotIds
  );
  const totalViews = viewsRes ? viewsRes.count : 0;

  // Inquiries count & Leads
  const inqRows = await db.query(`
    SELECT i.*, p.title as plot_title, c.name as country_name
    FROM inquiries i
    JOIN plots p ON i.plot_id = p.id
    JOIN countries c ON p.country_id = c.id
    WHERE i.plot_id IN (${placeholders})
    ORDER BY i.timestamp DESC
  `, plotIds);

  const totalInquiries = inqRows.length;
  const rate = totalViews > 0 ? ((totalInquiries / totalViews) * 100).toFixed(1) : '0.0';

  // Last 7 Days Chart
  const viewsChart = [];
  for (let i = 6; i >= 0; i--) {
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() - i);
    const datePrefix = targetDate.toISOString().slice(0, 10); // YYYY-MM-DD

    const dayViews = await db.queryFirst(`
      SELECT COUNT(*) as count 
      FROM plot_views 
      WHERE plot_id IN (${placeholders}) AND timestamp LIKE ?
    `, [...plotIds, `${datePrefix}%`]);

    viewsChart.push({
      day: targetDate.toLocaleDateString('en-US', { weekday: 'short' }),
      count: dayViews ? dayViews.count : 0,
      active: i === 0
    });
  }

  return c.json({
    totalViews,
    totalInquiries,
    conversionRate: rate,
    leads: inqRows.map(row => serializeInquiry(row, row.plot_title, row.country_name)),
    viewsChart
  });
});

// ==========================================
// 5. ADMIN USER MANAGEMENT & DIRECTORY
// ==========================================

// Get Pending Users (Admin Only)
app.get('/api/admin/pending-users', async (c) => {
  const db = getDb(c.env);
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const pending = await db.query('SELECT * FROM users WHERE is_approved = 0');
  return c.json(pending.map(u => ({
    username: u.username,
    role: u.role,
    label: u.username,
    is_approved: false,
    is_suspended: Boolean(u.is_suspended)
  })));
});

// Approve User (Admin Only)
app.post('/api/admin/approve-user/:username', async (c) => {
  const db = getDb(c.env);
  const username = c.req.param('username');
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const user = await db.queryFirst('SELECT * FROM users WHERE username = ?', [username]);
  if (!user) return c.json({ detail: 'User not found' }, 404);

  await db.execute('UPDATE users SET is_approved = 1 WHERE username = ?', [username]);
  return c.json({ status: 'success', message: `User ${username} has been approved.` });
});

// Get All Users Directory (Admin Only)
app.get('/api/admin/users', async (c) => {
  const db = getDb(c.env);
  const userRole = c.req.header('x-user-role') || '';
  const currentAdmin = c.req.header('x-user-username') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const users = await db.query('SELECT * FROM users WHERE username != ?', [currentAdmin]);
  return c.json(users.map(u => ({
    username: u.username,
    role: u.role,
    label: u.username,
    is_approved: Boolean(u.is_approved),
    is_suspended: Boolean(u.is_suspended)
  })));
});

// Toggle Suspend User (Admin Only)
app.post('/api/admin/users/:username/suspend', async (c) => {
  const db = getDb(c.env);
  const username = c.req.param('username');
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const user = await db.queryFirst('SELECT * FROM users WHERE username = ?', [username]);
  if (!user) return c.json({ detail: 'User not found' }, 404);

  const nextSuspended = user.is_suspended ? 0 : 1;
  await db.execute('UPDATE users SET is_suspended = ? WHERE username = ?', [nextSuspended, username]);

  return c.json({
    status: 'success',
    is_suspended: Boolean(nextSuspended),
    message: `User ${username} suspension status toggled.`
  });
});

// Delete User Account (Admin Only)
app.delete('/api/admin/users/:username', async (c) => {
  const db = getDb(c.env);
  const username = c.req.param('username');
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const user = await db.queryFirst('SELECT * FROM users WHERE username = ?', [username]);
  if (!user) return c.json({ detail: 'User not found' }, 404);

  // Cascade delete plots & inquiries
  const plots = await db.query('SELECT id FROM plots WHERE owner_username = ?', [username]);
  for (const p of plots) {
    await db.execute('DELETE FROM inquiries WHERE plot_id = ?', [p.id]);
    await db.execute('DELETE FROM plot_views WHERE plot_id = ?', [p.id]);
  }
  await db.execute('DELETE FROM plots WHERE owner_username = ?', [username]);
  await db.execute('DELETE FROM users WHERE username = ?', [username]);

  return c.json({ status: 'success', message: `User ${username} and their listings have been deleted.` });
});

// Get Notifications (Admin Only)
app.get('/api/admin/notifications', async (c) => {
  const db = getDb(c.env);
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  const notifs = await db.query('SELECT * FROM notifications ORDER BY timestamp DESC');
  return c.json(notifs.map(n => ({
    id: n.id,
    message: n.message,
    read: Boolean(n.read),
    timestamp: n.timestamp
  })));
});

// Mark Notification Read (Admin Only)
app.post('/api/admin/notifications/:notif_id/read', async (c) => {
  const db = getDb(c.env);
  const notifId = c.req.param('notif_id');
  const userRole = c.req.header('x-user-role') || '';
  if (userRole !== 'admin') return c.json({ detail: 'Admin access required' }, 403);

  await db.execute('UPDATE notifications SET read = 1 WHERE id = ?', [notifId]);
  return c.json({ status: 'success' });
});

export default app;
