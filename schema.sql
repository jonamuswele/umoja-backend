-- Database Schema for Umoja Terra (SQLite / Cloudflare D1)

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'owner',
    is_approved INTEGER NOT NULL DEFAULT 0,
    is_suspended INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS countries (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    flag TEXT DEFAULT '🌍',
    motto TEXT,
    accent TEXT,
    desc TEXT,
    video_url TEXT,
    highlights TEXT DEFAULT '[]',
    potential_neighborhoods TEXT DEFAULT '[]',
    culture_info TEXT DEFAULT '{}',
    is_visible INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS plots (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    size TEXT NOT NULL,
    price REAL NOT NULL,
    neighborhood TEXT NOT NULL,
    owner_username TEXT NOT NULL,
    country_id TEXT NOT NULL,
    photos TEXT DEFAULT '[]',
    is_visible INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(country_id) REFERENCES countries(id),
    FOREIGN KEY(owner_username) REFERENCES users(username)
);

CREATE TABLE IF NOT EXISTS inquiries (
    id TEXT PRIMARY KEY,
    plot_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    current_city TEXT,
    message TEXT NOT NULL,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(plot_id) REFERENCES plots(id)
);

CREATE TABLE IF NOT EXISTS plot_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(plot_id) REFERENCES plots(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    message TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);
