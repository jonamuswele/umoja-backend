import json
import datetime
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from database import engine, get_db
import models
import schemas

app = FastAPI(title="Umoja Terra Backend API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
        "photos": json.loads(p.photos or "[]")
    }

def serialize_country(c: models.Country) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "motto": c.motto,
        "accent": c.accent,
        "desc": c.desc,
        "videoUrl": c.video_url,
        "highlights": json.loads(c.highlights or "[]"),
        "potentialNeighborhoods": json.loads(c.potential_neighborhoods or "[]"),
        "cultureInfo": json.loads(c.culture_info or "{}"),
        "plots": [serialize_plot(p) for p in c.plots]
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

# --- ENDPOINTS ---

# 1. Login & Registration
@app.post("/api/auth/login", response_model=schemas.UserResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    password = payload.password
    
    # Check admin
    if username == "admin" and password == "admin":
        return {"username": "admin", "role": "admin", "label": "Console Admin"}
        
    # Check DB
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        if user.password_hash == password:
            return {"username": user.username, "role": user.role, "label": payload.username}
        else:
            raise HTTPException(status_code=400, detail="Incorrect password")
            
    # Auto register owner if password matches landlord template
    if password == "umoja" and len(username) >= 3:
        new_user = models.User(username=username, password_hash="umoja", role="owner")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"username": new_user.username, "role": "owner", "label": payload.username}
        
    raise HTTPException(status_code=400, detail="Incorrect credentials. Landowners use password 'umoja'.")

# 2. Get Countries Directory
@app.get("/api/countries", response_model=List[schemas.CountryResponse])
def get_countries(db: Session = Depends(get_db)):
    countries = db.query(models.Country).all()
    return [serialize_country(c) for c in countries]

# 3. Create New Plot Listing
@app.post("/api/plots", response_model=schemas.PlotResponse)
def create_plot(
    payload: schemas.PlotCreate,
    x_user_username: str = Header(..., description="Logged in username"),
    x_user_role: str = Header(..., description="Logged in role"),
    db: Session = Depends(get_db)
):
    if x_user_role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
        
    country = db.query(models.Country).filter(models.Country.id == payload.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
        
    plot_id = f"plot-{int(datetime.datetime.utcnow().timestamp())}"
    new_plot = models.Plot(
        id=plot_id,
        title=payload.title,
        size=payload.size,
        price=payload.price,
        neighborhood=payload.neighborhood,
        owner_username=x_user_username,
        country_id=payload.country_id,
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
