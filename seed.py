import json
from app.database import SessionLocal, engine, Base
from app import models

# Drop and recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 1. Seed Only the approved System Admin
    admin_user = models.User(
        username="admin", 
        password_hash="admin", 
        role="admin",
        is_approved=True
    )
    db.add(admin_user)
    db.commit()
    print("Database successfully reset to a clean slate with one pre-approved 'admin' user!")
except Exception as e:
    db.rollback()
    print("Seeding failed:", e)
finally:
    db.close()
