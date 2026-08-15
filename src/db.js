import fs from 'fs';
import path from 'path';

let localData = null;
const DB_FILE = path.resolve(process.cwd(), 'umoja_terra_data.json');

function initLocalData() {
  if (localData) return;
  if (fs.existsSync(DB_FILE)) {
    try {
      localData = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    } catch (e) {
      localData = getDefaultData();
    }
  } else {
    localData = getDefaultData();
    saveLocalData();
  }
}

function saveLocalData() {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(localData, null, 2), 'utf8');
  } catch (e) {
    console.error("Failed to persist local DB:", e);
  }
}

function getDefaultData() {
  return {
    users: [
      {
        username: 'admin',
        password_hash: 'admin',
        role: 'admin',
        is_approved: 1,
        is_suspended: 0
      }
    ],
    countries: [],
    plots: [],
    inquiries: [],
    plot_views: [],
    notifications: []
  };
}

/**
 * Universal Database Adapter:
 * 1. Uses Cloudflare D1 SQL queries when deployed to Cloudflare Workers (c.env.DB)
 * 2. Uses pure JavaScript JSON storage when running locally in Node.js (zero C++ dependencies)
 */
export function getDb(env) {
  // 1. Cloudflare Workers D1 Mode
  if (env && env.DB) {
    const d1 = env.DB;
    return {
      async query(sql, params = []) {
        const stmt = d1.prepare(sql).bind(...params);
        const result = await stmt.all();
        return result.results || [];
      },
      async queryFirst(sql, params = []) {
        const stmt = d1.prepare(sql).bind(...params);
        return await stmt.first();
      },
      async execute(sql, params = []) {
        const stmt = d1.prepare(sql).bind(...params);
        return await stmt.run();
      }
    };
  }

  // 2. Local Node.js Mode (Pure JS)
  initLocalData();

  return {
    async query(sql, params = []) {
      const s = sql.trim().toUpperCase();

      if (s.startsWith('SELECT * FROM COUNTRIES')) {
        if (s.includes('WHERE ID =')) {
          const id = params[0];
          return localData.countries.filter(c => c.id === id);
        }
        return [...localData.countries];
      }

      if (s.startsWith('SELECT * FROM PLOTS')) {
        if (s.includes('WHERE COUNTRY_ID =')) {
          const cid = params[0];
          return localData.plots.filter(p => p.country_id === cid);
        }
        if (s.includes('WHERE OWNER_USERNAME =')) {
          const owner = params[0];
          return localData.plots.filter(p => p.owner_username === owner);
        }
        return [...localData.plots];
      }

      if (s.startsWith('SELECT ID FROM PLOTS')) {
        if (s.includes('WHERE OWNER_USERNAME =')) {
          const owner = params[0];
          return localData.plots.filter(p => p.owner_username === owner).map(p => ({ id: p.id }));
        }
        return localData.plots.map(p => ({ id: p.id }));
      }

      if (s.startsWith('SELECT * FROM USERS')) {
        if (s.includes('WHERE IS_APPROVED = 0')) {
          return localData.users.filter(u => !u.is_approved);
        }
        if (s.includes('WHERE USERNAME !=')) {
          const current = params[0];
          return localData.users.filter(u => u.username !== current);
        }
        return [...localData.users];
      }

      if (s.startsWith('SELECT * FROM NOTIFICATIONS')) {
        return [...localData.notifications].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      }

      if (s.startsWith('SELECT I.*')) {
        let inqs = [...localData.inquiries];
        if (s.includes('WHERE P.OWNER_USERNAME =')) {
          const owner = params[0];
          const ownerPlotIds = new Set(localData.plots.filter(p => p.owner_username === owner).map(p => p.id));
          inqs = inqs.filter(i => ownerPlotIds.has(i.plot_id));
        } else if (s.includes('WHERE I.PLOT_ID IN')) {
          const allowedIds = new Set(params);
          inqs = inqs.filter(i => allowedIds.has(i.plot_id));
        }
        return inqs.map(i => {
          const plot = localData.plots.find(p => p.id === i.plot_id);
          const country = plot ? localData.countries.find(c => c.id === plot.country_id) : null;
          return {
            ...i,
            plot_title: plot ? plot.title : 'Unknown Plot',
            country_name: country ? country.name : 'Unknown'
          };
        }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      }

      return [];
    },

    async queryFirst(sql, params = []) {
      const s = sql.trim().toUpperCase();

      if (s.startsWith('SELECT * FROM USERS WHERE USERNAME =')) {
        const u = params[0];
        return localData.users.find(user => user.username === u) || null;
      }

      if (s.startsWith('SELECT * FROM COUNTRIES WHERE ID =')) {
        const id = params[0];
        return localData.countries.find(c => c.id === id) || null;
      }

      if (s.startsWith('SELECT * FROM PLOTS WHERE ID =')) {
        const id = params[0];
        return localData.plots.find(p => p.id === id) || null;
      }

      if (s.startsWith('SELECT * FROM INQUIRIES WHERE ID =')) {
        const id = params[0];
        return localData.inquiries.find(i => i.id === id) || null;
      }

      if (s.startsWith('SELECT * FROM NOTIFICATIONS WHERE ID =')) {
        const id = params[0];
        return localData.notifications.find(n => n.id === id) || null;
      }

      if (s.includes('COUNT(*) AS COUNT FROM PLOT_VIEWS')) {
        let views = localData.plot_views;
        if (s.includes('AND TIMESTAMP LIKE')) {
          const datePrefix = params[params.length - 1].replace('%', '');
          const plotIds = new Set(params.slice(0, -1));
          views = views.filter(v => plotIds.has(v.plot_id) && v.timestamp.startsWith(datePrefix));
        } else if (s.includes('WHERE PLOT_ID IN')) {
          const plotIds = new Set(params);
          views = views.filter(v => plotIds.has(v.plot_id));
        }
        return { count: views.length };
      }

      const res = await this.query(sql, params);
      return res.length > 0 ? res[0] : null;
    },

    async execute(sql, params = []) {
      const s = sql.trim().toUpperCase();

      // INSERT USERS
      if (s.startsWith('INSERT INTO USERS')) {
        const [username, password_hash, role, is_approved, is_suspended] = params;
        localData.users.push({ username, password_hash, role, is_approved, is_suspended });
        saveLocalData();
        return;
      }

      // INSERT COUNTRIES
      if (s.startsWith('INSERT INTO COUNTRIES')) {
        const [id, name, flag, motto, accent, desc, video_url, highlights, potential_neighborhoods, culture_info, is_visible] = params;
        localData.countries.push({
          id, name, flag, motto, accent, desc, video_url,
          highlights, potential_neighborhoods, culture_info, is_visible
        });
        saveLocalData();
        return;
      }

      // UPDATE COUNTRIES
      if (s.startsWith('UPDATE COUNTRIES SET')) {
        if (s.includes('IS_VISIBLE = ?')) {
          const [nextVis, cid] = params;
          const country = localData.countries.find(c => c.id === cid);
          if (country) country.is_visible = nextVis;
        } else {
          const [motto, desc, video_url, accent, flag, highlights, potential_neighborhoods, culture_info, id] = params;
          const country = localData.countries.find(c => c.id === id);
          if (country) {
            Object.assign(country, { motto, desc, video_url, accent, flag, highlights, potential_neighborhoods, culture_info });
          }
        }
        saveLocalData();
        return;
      }

      // INSERT PLOTS
      if (s.startsWith('INSERT INTO PLOTS')) {
        const [id, title, size, price, neighborhood, owner_username, country_id, photos, is_visible] = params;
        localData.plots.push({ id, title, size, price, neighborhood, owner_username, country_id, photos, is_visible });
        saveLocalData();
        return;
      }

      // UPDATE PLOTS
      if (s.startsWith('UPDATE PLOTS SET')) {
        if (s.includes('IS_VISIBLE = ?')) {
          const [nextVis, pid] = params;
          const plot = localData.plots.find(p => p.id === pid);
          if (plot) plot.is_visible = nextVis;
        } else {
          const [title, size, price, neighborhood, photos, id] = params;
          const plot = localData.plots.find(p => p.id === id);
          if (plot) {
            Object.assign(plot, { title, size, price, neighborhood, photos });
          }
        }
        saveLocalData();
        return;
      }

      // DELETE PLOTS
      if (s.startsWith('DELETE FROM PLOTS WHERE ID =')) {
        const pid = params[0];
        localData.plots = localData.plots.filter(p => p.id !== pid);
        saveLocalData();
        return;
      }

      if (s.startsWith('DELETE FROM PLOTS WHERE OWNER_USERNAME =')) {
        const owner = params[0];
        localData.plots = localData.plots.filter(p => p.owner_username !== owner);
        saveLocalData();
        return;
      }

      // INSERT INQUIRIES
      if (s.startsWith('INSERT INTO INQUIRIES')) {
        const [id, plot_id, full_name, email, phone, current_city, message, type, timestamp] = params;
        localData.inquiries.push({ id, plot_id, full_name, email, phone, current_city, message, type, timestamp });
        saveLocalData();
        return;
      }

      // INSERT PLOT_VIEWS
      if (s.startsWith('INSERT INTO PLOT_VIEWS')) {
        const [plot_id, timestamp] = params;
        localData.plot_views.push({ id: localData.plot_views.length + 1, plot_id, timestamp });
        saveLocalData();
        return;
      }

      // INSERT NOTIFICATIONS
      if (s.startsWith('INSERT INTO NOTIFICATIONS')) {
        const [id, message, read, timestamp] = params;
        localData.notifications.push({ id, message, read, timestamp });
        saveLocalData();
        return;
      }

      // UPDATE NOTIFICATIONS
      if (s.startsWith('UPDATE NOTIFICATIONS SET READ = 1 WHERE ID = ?')) {
        const notifId = params[0];
        const notif = localData.notifications.find(n => n.id === notifId);
        if (notif) notif.read = 1;
        saveLocalData();
        return;
      }

      // UPDATE USERS
      if (s.startsWith('UPDATE USERS SET IS_APPROVED = 1 WHERE USERNAME = ?')) {
        const uname = params[0];
        const u = localData.users.find(user => user.username === uname);
        if (u) u.is_approved = 1;
        saveLocalData();
        return;
      }

      if (s.startsWith('UPDATE USERS SET IS_SUSPENDED = ? WHERE USERNAME = ?')) {
        const [susp, uname] = params;
        const u = localData.users.find(user => user.username === uname);
        if (u) u.is_suspended = susp;
        saveLocalData();
        return;
      }

      // DELETE USERS
      if (s.startsWith('DELETE FROM USERS WHERE USERNAME = ?')) {
        const uname = params[0];
        localData.users = localData.users.filter(u => u.username !== uname);
        saveLocalData();
        return;
      }

      // RESET / TRUNCATE
      if (s.startsWith('DELETE FROM')) {
        if (s.includes('PLOT_VIEWS')) localData.plot_views = [];
        if (s.includes('INQUIRIES')) localData.inquiries = [];
        if (s.includes('PLOTS')) localData.plots = [];
        if (s.includes('COUNTRIES')) localData.countries = [];
        if (s.includes('NOTIFICATIONS')) localData.notifications = [];
        if (s.includes('USERS')) localData.users = [];
        saveLocalData();
      }
    }
  };
}
