import json
import datetime
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from database import init_db
from models import User, Country, Plot, Inquiry, Notification

app = FastAPI(title="Umoja Terra Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

AFRICAN_FLAGS = {
    "algeria": "🇩🇿", "angola": "🇦🇴", "benin": "🇧🇯", "botswana": "🇧🇼", "burkina-faso": "🇧🇫",
    "burundi": "🇧🇮", "cabo-verde": "🇨🇻", "cameroon": "🇨🇲", "central-african-republic": "🇨🇫",
    "chad": "🇹🇩", "comoros": "🇰🇲", "congo-brazzaville": "🇨🇬", "congo-kinshasa": "🇨🇩",
    "drc": "🇨🇩", "drc-(congo)": "🇨🇩", "djibouti": "🇩🇯", "egypt": "🇪🇬", "equatorial-guinea": "🇬🇶",
    "eritrea": "🇪🇷", "eswatini": "🇸🇿", "ethiopia": "🇪🇹", "gabon": "🇬🇦", "gambia": "🇬🇲",
    "ghana": "🇬🇭", "guinea": "🇬🇳", "guinea-bissau": "🇬🇼", "ivory-coast": "🇨🇮", "kenya": "🇰🇪",
    "lesotho": "🇱🇸", "liberia": "🇱🇷", "libya": "🇱🇾", "madagascar": "🇲🇬", "malawi": "🇲🇼",
    "mali": "🇲🇱", "mauritania": "🇲🇷", "mauritius": "🇲🇺", "morocco": "🇲🇦", "mozambique": "🇲🇿",
    "namibia": "🇳🇦", "niger": "🇳🇪", "nigeria": "🇳🇬", "rwanda": "🇷🇼", "sao-tome-and-principe": "🇸🇹",
    "senegal": "🇸🇳", "seychelles": "🇸🇨", "sierra-leone": "🇸🇱", "somalia": "🇸🇴", "south-africa": "🇿🇦",
    "south-sudan": "🇸🇸", "sudan": "🇸🇩", "tanzania": "🇹🇿", "togo": "🇹🇬", "tunisia": "🇹🇳",
    "uganda": "🇺🇬", "zambia": "🇿🇲", "zimbabwe": "🇿🇼"
}


# ─── D1 helpers ──────────────────────────────────────────────────────────────

def get_db(request: Request):
    """Extract the D1 binding from the request scope (injected by Cloudflare Workers)."""
    env = request.scope.get("env")
    if env is None:
        raise HTTPException(status_code=500, detail="D1 env binding not available")
    return env.DB


async def d1_first(db, sql: str, *params) -> Optional[dict]:
    """Run a query and return the first row as a dict, or None."""
    stmt = db.prepare(sql)
    if params:
        stmt = stmt.bind(*params)
    result = await stmt.first()
    return result


async def d1_all(db, sql: str, *params) -> List[dict]:
    """Run a query and return all rows as a list of dicts."""
    stmt = db.prepare(sql)
    if params:
        stmt = stmt.bind(*params)
    result = await stmt.all()
    return result.results if result.results else []


async def d1_run(db, sql: str, *params):
    """Run an INSERT / UPDATE / DELETE statement."""
    stmt = db.prepare(sql)
    if params:
        stmt = stmt.bind(*params)
    await stmt.run()


# ─── Serializers ─────────────────────────────────────────────────────────────

def serialize_plot(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "size": row.get("size"),
        "price": row["price"],
        "neighborhood": row.get("neighborhood"),
        "owner_username": row["owner_username"],
        "country_id": row["country_id"],
        "photos": json.loads(row.get("photos") or "[]"),
        "isVisible": bool(row.get("is_visible", 1)),
    }


def serialize_country(row: dict, plots: List[dict]) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "flag": row.get("flag") or "🌍",
        "motto": row.get("motto"),
        "accent": row.get("accent"),
        "desc": row.get("desc"),
        "videoUrl": row.get("video_url"),
        "highlights": json.loads(row.get("highlights") or "[]"),
        "potentialNeighborhoods": json.loads(row.get("potential_neighborhoods") or "[]"),
        "cultureInfo": json.loads(row.get("culture_info") or "{}"),
        "plots": plots,
        "isVisible": bool(row.get("is_visible", 1)),
    }


def serialize_inquiry(row: dict) -> dict:
    return {
        "id": row["id"],
        "plot_id": row["plot_id"],
        "plotTitle": row.get("plot_title") or "Unknown Plot",
        "fullName": row["full_name"],
        "email": row["email"],
        "phone": row.get("phone"),
        "currentCity": row.get("current_city"),
        "message": row.get("message"),
        "type": row["type"],
        "timestamp": row["timestamp"] + "Z",
        "countryName": row.get("country_name") or "Unknown",
    }


def now_iso() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def now_ts() -> int:
    return int(datetime.datetime.utcnow().timestamp())


# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # Tables are initialised via the D1 migration / wrangler d1 execute command.
    # init_db() can also be called manually from entry.py if needed.
    pass


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(request: Request):
    db = get_db(request)
    body = await request.json()
    username = body.get("username", "").strip().lower()
    password = body.get("password", "")
    label = body.get("label", "").strip()

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    existing = await d1_first(db, "SELECT id FROM users WHERE username = ?", username)
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")

    await d1_run(
        db,
        "INSERT INTO users (username, password_hash, role, is_approved, is_suspended) VALUES (?, ?, 'owner', 0, 0)",
        username, password,
    )

    notif_id = f"notif-reg-{username}-{now_ts()}"
    await d1_run(
        db,
        "INSERT INTO notifications (id, message, read, timestamp) VALUES (?, ?, 0, ?)",
        notif_id,
        f"New registration request: '{username}' ({label}) is awaiting approval.",
        now_iso(),
    )

    return {"username": username, "role": "owner", "label": label, "is_approved": False, "is_suspended": False}


@app.post("/api/auth/login")
async def login(request: Request):
    db = get_db(request)
    body = await request.json()
    username = body.get("username", "").strip().lower()
    password = body.get("password", "")

    row = await d1_first(db, "SELECT * FROM users WHERE username = ?", username)
    if not row:
        raise HTTPException(status_code=400, detail="Incorrect credentials. Please register first.")
    if row["password_hash"] != password:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if row["is_suspended"]:
        raise HTTPException(status_code=403, detail="Your account has been suspended by the administrator.")
    if not row["is_approved"]:
        raise HTTPException(status_code=403, detail="Your landowner account is pending administrator approval.")

    return {
        "username": row["username"],
        "role": row["role"],
        "label": row["username"],
        "is_approved": bool(row["is_approved"]),
        "is_suspended": bool(row["is_suspended"]),
    }


# ─── Countries ───────────────────────────────────────────────────────────────

@app.get("/api/countries")
async def get_countries(
    request: Request,
    x_user_role: Optional[str] = Header(None),
    x_user_username: Optional[str] = Header(None),
):
    db = get_db(request)
    countries = await d1_all(db, "SELECT * FROM countries")
    result = []

    for c in countries:
        if x_user_role != "admin" and not c.get("is_visible"):
            continue

        plots = await d1_all(db, "SELECT * FROM plots WHERE country_id = ?", c["id"])
        filtered_plots = []
        for p in plots:
            if x_user_role == "admin" or p.get("is_visible") or (x_user_username and p["owner_username"] == x_user_username):
                filtered_plots.append(serialize_plot(p))

        result.append(serialize_country(c, filtered_plots))

    return result


@app.post("/api/countries")
async def create_country(
    request: Request,
    x_user_role: str = Header(...),
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only the main admin can add new countries")

    db = get_db(request)
    body = await request.json()
    name = body.get("name", "").strip()
    flag_input = body.get("flag", "").strip()

    country_id = name.lower().replace(" ", "-")
    existing = await d1_first(db, "SELECT id FROM countries WHERE id = ?", country_id)
    if existing:
        raise HTTPException(status_code=400, detail="Country already exists")

    flag = AFRICAN_FLAGS.get(country_id, flag_input or "🌍")
    culture = json.dumps({
        "whyLive": f"Live here to participate in {name}'s rising market.",
        "bestBuild": "Modern Eco-Villas or architectural designs matching the local topography.",
        "culture": "Warm hospitality, rich regional traditions, and community values.",
        "culturePhotos": [],
    })

    await d1_run(
        db,
        """INSERT INTO countries (id, name, flag, motto, accent, desc, video_url, highlights, potential_neighborhoods, culture_info, is_visible)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        country_id, name, flag,
        "A Vibrant New Region", "#1A3E26",
        f"Welcome to {name}. Explore vetted, high-value investment plots across premium zones in this growing region.",
        "https://www.w3schools.com/html/mov_bbb.mp4",
        json.dumps(["Secure Ownership", "Vetted Surveyor Beacons", "Gated Access"]),
        json.dumps([]),
        culture,
    )

    row = await d1_first(db, "SELECT * FROM countries WHERE id = ?", country_id)
    return serialize_country(row, [])


@app.put("/api/countries/{country_id}")
async def update_country(
    country_id: str,
    request: Request,
    x_user_role: str = Header(...),
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only the main admin can customize country landing pages")

    db = get_db(request)
    row = await d1_first(db, "SELECT id FROM countries WHERE id = ?", country_id)
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")

    body = await request.json()
    culture_info = body.get("cultureInfo", {})
    culture_json = json.dumps({
        "whyLive": culture_info.get("whyLive", ""),
        "bestBuild": culture_info.get("bestBuild", ""),
        "culture": culture_info.get("culture", ""),
        "culturePhotos": culture_info.get("culturePhotos", []),
    })

    await d1_run(
        db,
        """UPDATE countries SET motto=?, desc=?, video_url=?, accent=?, flag=?,
           highlights=?, potential_neighborhoods=?, culture_info=? WHERE id=?""",
        body.get("motto"), body.get("desc"), body.get("videoUrl"),
        body.get("accent"), body.get("flag"),
        json.dumps(body.get("highlights", [])),
        json.dumps(body.get("potentialNeighborhoods", [])),
        culture_json, country_id,
    )

    updated = await d1_first(db, "SELECT * FROM countries WHERE id = ?", country_id)
    plots = await d1_all(db, "SELECT * FROM plots WHERE country_id = ?", country_id)
    return serialize_country(updated, [serialize_plot(p) for p in plots])


@app.post("/api/admin/countries/{country_id}/visibility")
async def toggle_country_visibility(
    country_id: str,
    request: Request,
    x_user_role: str = Header(...),
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db(request)
    row = await d1_first(db, "SELECT is_visible FROM countries WHERE id = ?", country_id)
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")

    new_val = 0 if row["is_visible"] else 1
    await d1_run(db, "UPDATE countries SET is_visible = ? WHERE id = ?", new_val, country_id)
    return {"status": "success", "isVisible": bool(new_val)}


# ─── Plots ────────────────────────────────────────────────────────────────────

@app.post("/api/plots")
async def create_plot(
    request: Request,
    x_user_username: str = Header(...),
    x_user_role: str = Header(...),
):
    if x_user_role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    db = get_db(request)
    body = await request.json()
    country_name_raw = body.get("country_id", "").strip()
    if not country_name_raw:
        raise HTTPException(status_code=400, detail="Country name cannot be empty")

    country_slug = country_name_raw.lower().replace(" ", "-")
    country = await d1_first(db, "SELECT id FROM countries WHERE id = ?", country_slug)

    if not country:
        flag = AFRICAN_FLAGS.get(country_slug, "🌍")
        culture = json.dumps({
            "whyLive": f"Live here to participate in {country_name_raw}'s rising market.",
            "bestBuild": "Modern Eco-Villas or architectural designs matching the local topography.",
            "culture": "Warm hospitality, rich regional traditions, and community values.",
            "culturePhotos": [],
        })
        await d1_run(
            db,
            """INSERT INTO countries (id, name, flag, motto, accent, desc, video_url, highlights, potential_neighborhoods, culture_info, is_visible)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            country_slug, country_name_raw, flag,
            "A Vibrant New Region", "#1A3E26",
            f"Welcome to {country_name_raw}. Explore vetted, high-value investment plots across premium zones in this growing region.",
            "https://www.w3schools.com/html/mov_bbb.mp4",
            json.dumps(["Secure Ownership", "Vetted Surveyor Beacons", "Gated Access"]),
            json.dumps([]), culture,
        )
        notif_id = f"notif-country-{country_slug}-{now_ts()}"
        await d1_run(
            db,
            "INSERT INTO notifications (id, message, read, timestamp) VALUES (?, ?, 0, ?)",
            notif_id,
            f"Landowner added listings in '{country_name_raw}'. Landing page needs customization.",
            now_iso(),
        )

    plot_id = f"plot-{now_ts()}"
    await d1_run(
        db,
        "INSERT INTO plots (id, title, size, price, neighborhood, owner_username, country_id, photos, is_visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
        plot_id, body.get("title"), body.get("size"), body.get("price"),
        body.get("neighborhood"), x_user_username, country_slug,
        json.dumps(body.get("photos", [])),
    )

    row = await d1_first(db, "SELECT * FROM plots WHERE id = ?", plot_id)
    return serialize_plot(row)


@app.put("/api/plots/{plot_id}")
async def update_plot(
    plot_id: str,
    request: Request,
    x_user_username: str = Header(...),
    x_user_role: str = Header(...),
):
    db = get_db(request)
    plot = await d1_first(db, "SELECT * FROM plots WHERE id = ?", plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    if x_user_role != "admin" and plot["owner_username"] != x_user_username:
        raise HTTPException(status_code=403, detail="You do not own this listing")

    body = await request.json()
    await d1_run(
        db,
        "UPDATE plots SET title=?, size=?, price=?, neighborhood=?, photos=? WHERE id=?",
        body.get("title"), body.get("size"), body.get("price"),
        body.get("neighborhood"), json.dumps(body.get("photos", [])), plot_id,
    )

    row = await d1_first(db, "SELECT * FROM plots WHERE id = ?", plot_id)
    return serialize_plot(row)


@app.delete("/api/plots/{plot_id}")
async def delete_plot(
    plot_id: str,
    request: Request,
    x_user_username: str = Header(...),
    x_user_role: str = Header(...),
):
    db = get_db(request)
    plot = await d1_first(db, "SELECT * FROM plots WHERE id = ?", plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    if x_user_role != "admin" and plot["owner_username"] != x_user_username:
        raise HTTPException(status_code=403, detail="You do not own this listing")

    await d1_run(db, "DELETE FROM plot_views WHERE plot_id = ?", plot_id)
    await d1_run(db, "DELETE FROM inquiries WHERE plot_id = ?", plot_id)
    await d1_run(db, "DELETE FROM plots WHERE id = ?", plot_id)
    return {"status": "success", "message": f"Plot {plot_id} successfully deleted."}


@app.post("/api/plots/{plot_id}/view")
async def track_view(plot_id: str, request: Request):
    db = get_db(request)
    plot = await d1_first(db, "SELECT id FROM plots WHERE id = ?", plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    await d1_run(db, "INSERT INTO plot_views (plot_id, timestamp) VALUES (?, ?)", plot_id, now_iso())
    return {"status": "success"}


@app.post("/api/admin/plots/{plot_id}/visibility")
async def toggle_plot_visibility(
    plot_id: str,
    request: Request,
    x_user_role: str = Header(...),
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    db = get_db(request)
    row = await d1_first(db, "SELECT is_visible FROM plots WHERE id = ?", plot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Plot not found")

    new_val = 0 if row["is_visible"] else 1
    await d1_run(db, "UPDATE plots SET is_visible = ? WHERE id = ?", new_val, plot_id)
    return {"status": "success", "isVisible": bool(new_val)}


# ─── Inquiries ────────────────────────────────────────────────────────────────

@app.post("/api/inquiries")
async def create_inquiry(request: Request):
    db = get_db(request)
    body = await request.json()
    plot_id = body.get("plot_id")
    plot = await d1_first(db, "SELECT id FROM plots WHERE id = ?", plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    inq_id = f"inq-{now_ts()}"
    ts = now_iso()
    await d1_run(
        db,
        """INSERT INTO inquiries (id, plot_id, full_name, email, phone, current_city, message, type, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        inq_id, plot_id,
        body.get("fullName"), body.get("email"), body.get("phone"),
        body.get("currentCity"), body.get("message"), body.get("type"), ts,
    )

    row = await d1_first(
        db,
        """SELECT i.*, p.title as plot_title, c.name as country_name
           FROM inquiries i
           JOIN plots p ON i.plot_id = p.id
           JOIN countries c ON p.country_id = c.id
           WHERE i.id = ?""",
        inq_id,
    )
    return serialize_inquiry(row)


@app.get("/api/inquiries")
async def get_inquiries(
    request: Request,
    x_user_username: str = Header(...),
    x_user_role: str = Header(...),
):
    db = get_db(request)
    if x_user_role == "admin":
        rows = await d1_all(
            db,
            """SELECT i.*, p.title as plot_title, c.name as country_name
               FROM inquiries i
               JOIN plots p ON i.plot_id = p.id
               JOIN countries c ON p.country_id = c.id
               ORDER BY i.timestamp DESC""",
        )
    else:
        rows = await d1_all(
            db,
            """SELECT i.*, p.title as plot_title, c.name as country_name
               FROM inquiries i
               JOIN plots p ON i.plot_id = p.id
               JOIN countries c ON p.country_id = c.id
               WHERE p.owner_username = ?
               ORDER BY i.timestamp DESC""",
            x_user_username,
        )
    return [serialize_inquiry(r) for r in rows]


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

@app.get("/api/stats/dashboard")
async def get_dashboard_stats(
    request: Request,
    x_user_username: str = Header(...),
    x_user_role: str = Header(...),
):
    db = get_db(request)

    if x_user_role == "admin":
        plots = await d1_all(db, "SELECT id FROM plots")
    else:
        plots = await d1_all(db, "SELECT id FROM plots WHERE owner_username = ?", x_user_username)

    plot_ids = [p["id"] for p in plots]

    if not plot_ids:
        return {
            "totalViews": 0, "totalInquiries": 0, "conversionRate": "0.0",
            "leads": [], "viewsChart": [],
        }

    placeholders = ",".join(["?" for _ in plot_ids])

    views_count_row = await d1_first(
        db, f"SELECT COUNT(*) as cnt FROM plot_views WHERE plot_id IN ({placeholders})", *plot_ids
    )
    views_count = views_count_row["cnt"] if views_count_row else 0

    inq_count_row = await d1_first(
        db, f"SELECT COUNT(*) as cnt FROM inquiries WHERE plot_id IN ({placeholders})", *plot_ids
    )
    inq_count = inq_count_row["cnt"] if inq_count_row else 0

    rate = f"{((inq_count / views_count) * 100):.1f}" if views_count > 0 else "0.0"

    leads_rows = await d1_all(
        db,
        f"""SELECT i.*, p.title as plot_title, c.name as country_name
            FROM inquiries i
            JOIN plots p ON i.plot_id = p.id
            JOIN countries c ON p.country_id = c.id
            WHERE i.plot_id IN ({placeholders})
            ORDER BY i.timestamp DESC""",
        *plot_ids,
    )
    leads = [serialize_inquiry(r) for r in leads_rows]

    today = datetime.date.today()
    views_chart = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_start = day.strftime("%Y-%m-%dT00:00:00")
        day_end = day.strftime("%Y-%m-%dT23:59:59")
        cnt_row = await d1_first(
            db,
            f"""SELECT COUNT(*) as cnt FROM plot_views
                WHERE plot_id IN ({placeholders})
                AND timestamp >= ? AND timestamp <= ?""",
            *plot_ids, day_start, day_end,
        )
        views_chart.append({
            "day": day.strftime("%a"),
            "count": cnt_row["cnt"] if cnt_row else 0,
            "active": day == today,
        })

    return {
        "totalViews": views_count,
        "totalInquiries": inq_count,
        "conversionRate": rate,
        "leads": leads,
        "viewsChart": views_chart,
    }


# ─── Admin ────────────────────────────────────────────────────────────────────

@app.get("/api/admin/pending-users")
async def get_pending_users(request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    rows = await d1_all(db, "SELECT * FROM users WHERE is_approved = 0")
    return [{"username": r["username"], "role": r["role"], "label": r["username"], "is_approved": False} for r in rows]


@app.post("/api/admin/approve-user/{username}")
async def approve_user(username: str, request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    row = await d1_first(db, "SELECT id FROM users WHERE username = ?", username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    await d1_run(db, "UPDATE users SET is_approved = 1 WHERE username = ?", username)
    return {"status": "success", "message": f"User {username} has been approved."}


@app.get("/api/admin/users")
async def get_all_users(
    request: Request,
    x_user_role: str = Header(...),
    x_user_username: str = Header(...),
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    rows = await d1_all(db, "SELECT * FROM users WHERE username != ?", x_user_username)
    return [
        {"username": r["username"], "role": r["role"], "label": r["username"],
         "is_approved": bool(r["is_approved"]), "is_suspended": bool(r["is_suspended"])}
        for r in rows
    ]


@app.post("/api/admin/users/{username}/suspend")
async def toggle_suspend_user(username: str, request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    row = await d1_first(db, "SELECT is_suspended FROM users WHERE username = ?", username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    new_val = 0 if row["is_suspended"] else 1
    await d1_run(db, "UPDATE users SET is_suspended = ? WHERE username = ?", new_val, username)
    return {"status": "success", "is_suspended": bool(new_val), "message": f"User {username} suspension toggled."}


@app.delete("/api/admin/users/{username}")
async def delete_user(username: str, request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    row = await d1_first(db, "SELECT id FROM users WHERE username = ?", username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all plots by this user to cascade delete views/inquiries
    user_plots = await d1_all(db, "SELECT id FROM plots WHERE owner_username = ?", username)
    for p in user_plots:
        await d1_run(db, "DELETE FROM plot_views WHERE plot_id = ?", p["id"])
        await d1_run(db, "DELETE FROM inquiries WHERE plot_id = ?", p["id"])
    await d1_run(db, "DELETE FROM plots WHERE owner_username = ?", username)
    await d1_run(db, "DELETE FROM users WHERE username = ?", username)
    return {"status": "success", "message": f"User {username} and their listings have been deleted."}


@app.get("/api/admin/notifications")
async def get_notifications(request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    rows = await d1_all(db, "SELECT * FROM notifications ORDER BY timestamp DESC")
    return [{"id": r["id"], "message": r["message"], "read": bool(r["read"]), "timestamp": r["timestamp"]} for r in rows]


@app.post("/api/admin/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, request: Request, x_user_role: str = Header(...)):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    db = get_db(request)
    row = await d1_first(db, "SELECT id FROM notifications WHERE id = ?", notif_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    await d1_run(db, "UPDATE notifications SET read = 1 WHERE id = ?", notif_id)
    return {"status": "success"}
