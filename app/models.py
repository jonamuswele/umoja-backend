from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "admin" or "owner"
    is_approved = Column(Boolean, default=False)

    plots = relationship("Plot", back_populates="owner")

class Country(Base):
    __tablename__ = "countries"

    id = Column(String, primary_key=True, index=True)  # e.g., "kenya"
    name = Column(String, nullable=False)
    flag = Column(String, default="🌍")
    motto = Column(String)
    accent = Column(String)
    desc = Column(Text)
    video_url = Column(String)
    
    # Store lists and complex objects as JSON strings
    highlights = Column(Text)  # JSON List of strings
    potential_neighborhoods = Column(Text)  # JSON List of dicts
    culture_info = Column(Text)  # JSON dict

    plots = relationship("Plot", back_populates="country", cascade="all, delete-orphan")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Plot(Base):
    __tablename__ = "plots"

    id = Column(String, primary_key=True, index=True)  # e.g., "ke-nanyuki"
    title = Column(String, nullable=False)
    size = Column(String)
    price = Column(Float, nullable=False)
    neighborhood = Column(Text)
    owner_username = Column(String, ForeignKey("users.username"), nullable=False)
    country_id = Column(String, ForeignKey("countries.id"), nullable=False)
    photos = Column(Text)  # JSON List of dicts

    owner = relationship("User", back_populates="plots")
    country = relationship("Country", back_populates="plots")
    views = relationship("PlotView", back_populates="plot", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="plot", cascade="all, delete-orphan")

class PlotView(Base):
    __tablename__ = "plot_views"

    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(String, ForeignKey("plots.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    plot = relationship("Plot", back_populates="views")

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(String, primary_key=True, index=True)  # e.g., "inq-123456"
    plot_id = Column(String, ForeignKey("plots.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    current_city = Column(String)
    message = Column(Text)
    type = Column(String, nullable=False)  # "Buy" or "Negotiate"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    plot = relationship("Plot", back_populates="inquiries")
