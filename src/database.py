CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'owner',
        is_approved INTEGER NOT NULL DEFAULT 0,
        is_suspended INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS countries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        flag TEXT DEFAULT '🌍',
        motto TEXT,
        accent TEXT,
        desc TEXT,
        video_url TEXT,
        highlights TEXT,
        potential_neighborhoods TEXT,
        culture_info TEXT,
        is_visible INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS plots (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        size TEXT,
        price REAL NOT NULL,
        neighborhood TEXT,
        owner_username TEXT NOT NULL REFERENCES users(username),
        country_id TEXT NOT NULL REFERENCES countries(id),
        photos TEXT,
        is_visible INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS plot_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plot_id TEXT NOT NULL REFERENCES plots(id),
        timestamp TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inquiries (
        id TEXT PRIMARY KEY,
        plot_id TEXT NOT NULL REFERENCES plots(id),
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        current_city TEXT,
        message TEXT,
        type TEXT NOT NULL,
        timestamp TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        message TEXT NOT NULL,
        read INTEGER NOT NULL DEFAULT 0,
        timestamp TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
]


async def init_db(db):
    """
    Run once at startup (or on cold start) to ensure all tables exist.
    Call this from your entry.py or at the top of main.py via:
        await init_db(env.DB)
    """
    for sql in CREATE_TABLES_SQL:
        await db.prepare(sql.strip()).run()
