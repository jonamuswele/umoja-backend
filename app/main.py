import json
import datetime
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import engine, get_db
from app import models
from app import schemas

app = FastAPI(title="Umoja Terra Backend API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper serializers
def serialize_plot(p: models.Plot) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "size": p.size,
        "price": p.price,
        "neighborhood": p.neighborhood,
        "owner_username": p.owner_username,
        "country_id": p.country_id,
        "photos": json.loads(p.photos or "[]"),
        "isVisible": p.is_visible
    }

def serialize_country(c: models.Country) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "flag": c.flag or "🌍",
        "motto": c.motto,
        "accent": c.accent,
        "desc": c.desc,
        "videoUrl": c.video_url,
        "highlights": json.loads(c.highlights or "[]"),
        "potentialNeighborhoods": json.loads(c.potential_neighborhoods or "[]"),
        "cultureInfo": json.loads(c.culture_info or "{}"),
        "plots": [serialize_plot(p) for p in c.plots],
        "isVisible": c.is_visible
    }

def serialize_inquiry(inq: models.Inquiry) -> dict:
    return {
        "id": inq.id,
        "plot_id": inq.plot_id,
        "plotTitle": inq.plot.title if inq.plot else "Unknown Plot",
        "fullName": inq.full_name,
        "email": inq.email,
        "phone": inq.phone,
        "currentCity": inq.current_city,
        "message": inq.message,
        "type": inq.type,
        "timestamp": inq.timestamp.isoformat() + "Z",
        "countryName": inq.plot.country.name if inq.plot and inq.plot.country else "Unknown"
    }

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

# --- ENDPOINTS ---

# 1. Login & Registration
@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    label = payload.label.strip()
    
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")
        
    # Create inactive user (is_approved=False)
    new_user = models.User(
        username=username,
        password_hash=payload.password, # In production we hash, but here we match the mock pattern
        role="owner",
        is_approved=False
    )
    db.add(new_user)
    
    # Create admin notification
    notif_id = f"notif-reg-{username}-{int(datetime.datetime.utcnow().timestamp())}"
    notif = models.Notification(
        id=notif_id,
        message=f"New registration request: '{username}' ({label}) is awaiting approval."
    )
    db.add(notif)
    
    db.commit()
    db.refresh(new_user)
    return {
        "username": new_user.username,
        "role": new_user.role,
        "label": label,
        "is_approved": new_user.is_approved,
        "is_suspended": new_user.is_suspended
    }

@app.post("/api/auth/login", response_model=schemas.UserResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    password = payload.password
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials. Please register first.")
        
    if user.password_hash != password:
        raise HTTPException(status_code=400, detail="Incorrect password")
        
    if user.is_suspended:
        raise HTTPException(
            status_code=403,
            detail="Your account has been suspended by the administrator. Please contact support."
        )
        
    if not user.is_approved:
        raise HTTPException(
            status_code=403, 
            detail="Your landowner account is pending administrator approval."
        )
        
    return {
        "username": user.username,
        "role": user.role,
        "label": user.username,
        "is_approved": user.is_approved,
        "is_suspended": user.is_suspended
    }

# 2. Get Countries Directory
@app.get("/api/countries", response_model=List[schemas.CountryResponse])
def get_countries(
    x_user_role: Optional[str] = Header(None, description="Logged in role"),
    x_user_username: Optional[str] = Header(None, description="Logged in username"),
    db: Session = Depends(get_db)
):
    countries = db.query(models.Country).all()
    if x_user_role == "admin":
        return [serialize_country(c) for c in countries]
        
    res = []
    for c in countries:
        # If country is hidden, public users shouldn't see it at all
        if not c.is_visible:
            continue
            
        # Filter plots in this country
        filtered_plots = []
        for p in c.plots:
            # Plot must be visible, OR request must come from the owner of the plot
            if p.is_visible or (x_user_username and p.owner_username == x_user_username):
                filtered_plots.append(serialize_plot(p))
                
        c_dict = serialize_country(c)
        c_dict["plots"] = filtered_plots
        res.append(c_dict)
    return res

# 3. Create New Plot Listing (With Dynamic Country Creation)
@app.post("/api/plots", response_model=schemas.PlotResponse)
def create_plot(
    payload: schemas.PlotCreate,
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
        
    country_name_raw = payload.country_id.strip()
    if not country_name_raw:
        raise HTTPException(status_code=400, detail="Country name cannot be empty")
        
    # Generate clean, slugified key. E.g. "Sierra Leone" -> "sierra-leone"
    country_slug = country_name_raw.lower().replace(" ", "-")
    country = db.query(models.Country).filter(models.Country.id == country_slug).first()
    
    if not country:
        # Resolve flag emoji from the lookup dictionary
        flag_emoji = AFRICAN_FLAGS.get(country_slug, "🌍")
        
        # Create a new country dynamically with default settings
        country = models.Country(
            id=country_slug,
            name=country_name_raw,
            flag=flag_emoji,
            motto="A Vibrant New Region",
            accent="#1A3E26", # Default dark green
            desc=f"Welcome to {country_name_raw}. Explore vetted, high-value investment plots across premium zones in this growing region.",
            video_url="https://www.w3schools.com/html/mov_bbb.mp4",
            highlights=json.dumps(["Secure Ownership", "Vetted Surveyor Beacons", "Gated Access"]),
            potential_neighborhoods=json.dumps([]),
            culture_info=json.dumps({
                "whyLive": f"Live here to participate in {country_name_raw}'s rising market and beautiful community landscape.",
                "bestBuild": "Modern Eco-Villas or architectural designs matching the local topography.",
                "culture": "Warm hospitality, rich regional traditions, and community values.",
                "culturePhotos": []
            })
        )
        db.add(country)
        
        # Dispatch notification to the admin
        notif_id = f"notif-country-{country_slug}-{int(datetime.datetime.utcnow().timestamp())}"
        notif = models.Notification(
            id=notif_id,
            message=f"Landowner added listings in '{country_name_raw}'. Landing page needs customization."
        )
        db.add(notif)
        db.commit()
        db.refresh(country)
        
    plot_id = f"plot-{int(datetime.datetime.utcnow().timestamp())}"
    new_plot = models.Plot(
        id=plot_id,
        title=payload.title,
        size=payload.size,
        price=payload.price,
        neighborhood=payload.neighborhood,
        owner_username=x_user_username,
        country_id=country.id,
        photos=json.dumps([p.model_dump() for p in payload.photos])
    )
    
    db.add(new_plot)
    db.commit()
    db.refresh(new_plot)
    return serialize_plot(new_plot)

# 4. Edit Plot Specification
@app.put("/api/plots/{plot_id}", response_model=schemas.PlotResponse)
def update_plot(
    plot_id: str,
    payload: schemas.PlotUpdate,
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    plot = db.query(models.Plot).filter(models.Plot.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
        
    # Check permissions (only owner or admin can edit)
    if x_user_role != "admin" and plot.owner_username != x_user_username:
        raise HTTPException(status_code=403, detail="You do not own this listing")
        
    plot.title = payload.title
    plot.size = payload.size
    plot.price = payload.price
    plot.neighborhood = payload.neighborhood
    plot.photos = json.dumps([p.model_dump() for p in payload.photos])
    
    db.commit()
    db.refresh(plot)
    return serialize_plot(plot)

# 4b. Delete Plot Listing (Owner or Admin Only)
@app.delete("/api/plots/{plot_id}")
def delete_plot(
    plot_id: str,
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    plot = db.query(models.Plot).filter(models.Plot.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
        
    # Check permissions
    if x_user_role != "admin" and plot.owner_username != x_user_username:
        raise HTTPException(status_code=403, detail="You do not own this listing")
        
    db.delete(plot)
    db.commit()
    return {"status": "success", "message": f"Plot {plot_id} successfully deleted."}

# 5. Track Click/View
@app.post("/api/plots/{plot_id}/view")
def track_view(plot_id: str, db: Session = Depends(get_db)):
    plot = db.query(models.Plot).filter(models.Plot.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
        
    db.add(models.PlotView(plot_id=plot_id))
    db.commit()
    return {"status": "success"}

# 6. Dispatch Inquiry
@app.post("/api/inquiries", response_model=schemas.InquiryResponse)
def create_inquiry(payload: schemas.InquiryCreate, db: Session = Depends(get_db)):
    plot = db.query(models.Plot).filter(models.Plot.id == payload.plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
        
    inq_id = f"inq-{int(datetime.datetime.utcnow().timestamp())}"
    new_inq = models.Inquiry(
        id=inq_id,
        plot_id=payload.plot_id,
        full_name=payload.fullName,
        email=payload.email,
        phone=payload.phone,
        current_city=payload.currentCity,
        message=payload.message,
        type=payload.type,
        timestamp=datetime.datetime.utcnow()
    )
    
    db.add(new_inq)
    db.commit()
    db.refresh(new_inq)
    return serialize_inquiry(new_inq)

# 7. Get Tenant Inquiries/Leads List
@app.get("/api/inquiries", response_model=List[schemas.InquiryResponse])
def get_inquiries(
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Inquiry).join(models.Plot)
    if x_user_role != "admin":
        query = query.filter(models.Plot.owner_username == x_user_username)
        
    inquiries = query.order_by(models.Inquiry.timestamp.desc()).all()
    return [serialize_inquiry(inq) for inq in inquiries]

# 8. Get Tenant Dashboard Stats
@app.get("/api/stats/dashboard", response_model=schemas.DashboardStatsResponse)
def get_dashboard_stats(
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    # Get all plots owned by user (or all plots if admin)
    plots_query = db.query(models.Plot)
    if x_user_role != "admin":
        plots_query = plots_query.filter(models.Plot.owner_username == x_user_username)
    owned_plots = plots_query.all()
    owned_plot_ids = [p.id for p in owned_plots]
    
    # 1. Total Views
    views_count = db.query(models.PlotView).filter(models.PlotView.plot_id.in_(owned_plot_ids)).count() if owned_plot_ids else 0
    
    # 2. Total Inquiries
    inquiries_query = db.query(models.Inquiry).filter(models.Inquiry.plot_id.in_(owned_plot_ids)) if owned_plot_ids else None
    inquiries_count = inquiries_query.count() if inquiries_query else 0
    
    # 3. Conversion Rate
    rate = f"{((inquiries_count / views_count) * 100):.1f}" if views_count > 0 else "0.0"
    
    # 4. Leads List
    inquiries = inquiries_query.join(models.Plot).order_by(models.Inquiry.timestamp.desc()).all() if inquiries_query else []
    leads_list = [serialize_inquiry(inq) for inq in inquiries]
    
    # 5. Last 7 Days Clicks Chart
    today = datetime.date.today()
    days_list = []
    views_chart = []
    
    # Generate last 7 days list (date objects and names)
    for i in range(6, -1, -1):
        day_date = today - datetime.timedelta(days=i)
        days_list.append(day_date)
        
    # Get views grouped by date
    for d in days_list:
        day_start = datetime.datetime.combine(d, datetime.time.min)
        day_end = datetime.datetime.combine(d, datetime.time.max)
        
        # Query count for this day
        if owned_plot_ids:
            cnt = db.query(models.PlotView).filter(
                models.PlotView.plot_id.in_(owned_plot_ids),
                models.PlotView.timestamp >= day_start,
                models.PlotView.timestamp <= day_end
            ).count()
        else:
            cnt = 0
            
        views_chart.append({
            "day": d.strftime("%a"),  # e.g., "Mon"
            "count": cnt,
            "active": d == today
        })
        
    return {
        "totalViews": views_count,
        "totalInquiries": inquiries_count,
        "conversionRate": rate,
        "leads": leads_list,
        "viewsChart": views_chart
    }

# 10. Update Country Metadata (Admin Only)
@app.put("/api/countries/{country_id}", response_model=schemas.CountryResponse)
def update_country(
    country_id: str,
    payload: schemas.CountryUpdate,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only the main admin can customize country landing pages")
        
    country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
        
    country.motto = payload.motto
    country.desc = payload.desc
    country.video_url = payload.videoUrl
    country.accent = payload.accent
    country.flag = payload.flag
    country.highlights = json.dumps(payload.highlights)
    country.potential_neighborhoods = json.dumps([n.model_dump() for n in payload.potentialNeighborhoods])
    
    # Store cultureInfo properly
    country.culture_info = json.dumps({
        "whyLive": payload.cultureInfo.whyLive,
        "bestBuild": payload.cultureInfo.bestBuild,
        "culture": payload.cultureInfo.culture,
        "culturePhotos": [p.model_dump() for p in payload.cultureInfo.culturePhotos]
    })
    
    db.commit()
    db.refresh(country)
    return serialize_country(country)

# 11. Create a New Country (Admin Only)
@app.post("/api/countries", response_model=schemas.CountryResponse)
def create_country(
    payload: schemas.CountryCreateInput,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only the main admin can add new countries")
        
    country_id = payload.name.strip().lower().replace(" ", "-")
    existing = db.query(models.Country).filter(models.Country.id == country_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Country already exists")
        
    new_country = models.Country(
        id=country_id,
        name=payload.name.strip(),
        flag=AFRICAN_FLAGS.get(country_id, payload.flag.strip() or "🌍"),
        motto="A Vibrant New Region",
        accent="#1A3E26",
        desc=f"Welcome to {payload.name.strip()}. Explore vetted, high-value investment plots across premium zones in this growing region.",
        video_url="https://www.w3schools.com/html/mov_bbb.mp4",
        highlights=json.dumps(["Secure Ownership", "Vetted Surveyor Beacons", "Gated Access"]),
        potential_neighborhoods=json.dumps([]),
        culture_info=json.dumps({
            "whyLive": f"Live here to participate in {payload.name.strip()}'s rising market and beautiful community landscape.",
            "bestBuild": "Modern Eco-Villas or architectural designs matching the local topography.",
            "culture": "Warm hospitality, rich regional traditions, and community values.",
            "culturePhotos": []
        })
    )
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    return serialize_country(new_country)

# 12. Get Pending Approvals (Admin Only)
@app.get("/api/admin/pending-users", response_model=List[schemas.UserResponse])
def get_pending_users(
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    pending = db.query(models.User).filter(models.User.is_approved == False).all()
    return [
        {
            "username": u.username,
            "role": u.role,
            "label": u.username,
            "is_approved": u.is_approved
        }
        for u in pending
    ]

# 13. Approve User Registration (Admin Only)
@app.post("/api/admin/approve-user/{username}")
def approve_user(
    username: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    db.commit()
    return {"status": "success", "message": f"User {username} has been approved."}

# 14. Get System Notifications (Admin Only)
@app.get("/api/admin/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    notifs = db.query(models.Notification).order_by(models.Notification.timestamp.desc()).all()
    return notifs

# 15. Mark Notification as Read (Admin Only)
@app.post("/api/admin/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    db.commit()
    return {"status": "success"}

# 16. Get All Users (Admin Only)
@app.get("/api/admin/users", response_model=List[schemas.UserResponse])
def get_all_users(
    x_user_role: str = Header(..., description="Logged in role"),
    x_user_username: str = Header(..., description="Logged in username"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(models.User).filter(models.User.username != x_user_username).all()
    return [
        {
            "username": u.username,
            "role": u.role,
            "label": u.username,
            "is_approved": u.is_approved,
            "is_suspended": u.is_suspended
        }
        for u in users
    ]

# 17. Toggle Suspend User Account (Admin Only)
@app.post("/api/admin/users/{username}/suspend")
def toggle_suspend_user(
    username: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = not user.is_suspended
    db.commit()
    return {"status": "success", "is_suspended": user.is_suspended, "message": f"User {username} suspension status toggled."}

# 18. Delete User Account (Admin Only)
@app.delete("/api/admin/users/{username}")
def delete_user(
    username: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete their plots to cascade properly since database constraints require it
    db.query(models.Plot).filter(models.Plot.owner_username == username).delete()
    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User {username} and their listings have been deleted."}

# 19. Toggle Country Visibility (Admin Only)
@app.post("/api/admin/countries/{country_id}/visibility")
def toggle_country_visibility(
    country_id: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    country.is_visible = not country.is_visible
    db.commit()
    return {"status": "success", "isVisible": country.is_visible}

# 20. Toggle Plot Visibility (Admin Only)
@app.post("/api/admin/plots/{plot_id}/visibility")
def toggle_plot_visibility(
    plot_id: str,
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    plot = db.query(models.Plot).filter(models.Plot.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    plot.is_visible = not plot.is_visible
    db.commit()
    return {"status": "success", "isVisible": plot.is_visible}
