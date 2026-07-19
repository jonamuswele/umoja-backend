from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    label: str

class UserResponse(BaseModel):
    username: str
    role: str
    label: str
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)

class PhotoSchema(BaseModel):
    img: str
    rotate: float
    scale: float
    caption: str

class PlotCreate(BaseModel):
    title: str
    size: str
    price: float
    neighborhood: str
    country_id: str
    photos: List[PhotoSchema]

class PlotUpdate(BaseModel):
    title: str
    size: str
    price: float
    neighborhood: str
    photos: List[PhotoSchema]

class PlotResponse(BaseModel):
    id: str
    title: str
    size: str
    price: float
    neighborhood: str
    owner_username: str
    country_id: str
    photos: List[PhotoSchema]

    model_config = ConfigDict(from_attributes=True)

class InquiryCreate(BaseModel):
    plot_id: str
    fullName: str  # Matches front-end payload key
    email: str
    phone: Optional[str] = ""
    currentCity: Optional[str] = ""  # Matches front-end payload key
    message: Optional[str] = ""
    type: str  # "Buy" or "Negotiate" or "General"

class InquiryResponse(BaseModel):
    id: str
    plot_id: str
    plotTitle: str  # Matches front-end payload key
    fullName: str   # Matches front-end payload key
    email: str
    phone: Optional[str] = ""
    currentCity: Optional[str] = ""  # Matches front-end payload key
    message: Optional[str] = ""
    type: str
    timestamp: str  # ISO Format string
    countryName: str

    model_config = ConfigDict(from_attributes=True)

class PotentialNeighborhoodSchema(BaseModel):
    img: str
    caption: str

class CulturePhotoSchema(BaseModel):
    img: str
    rotate: float
    scale: float
    caption: str

class CultureInfoSchema(BaseModel):
    whyLive: str
    bestBuild: str
    culture: str
    culturePhotos: List[CulturePhotoSchema]

class CountryCreateInput(BaseModel):
    name: str
    flag: str

class CountryUpdate(BaseModel):
    motto: str
    desc: str
    videoUrl: str
    accent: str
    flag: str
    highlights: List[str]
    potentialNeighborhoods: List[PotentialNeighborhoodSchema]
    cultureInfo: CultureInfoSchema

class CountryResponse(BaseModel):
    id: str
    name: str
    flag: str
    motto: str
    accent: str
    desc: str
    videoUrl: str  # Matches front-end camelCase naming
    highlights: List[str]
    potentialNeighborhoods: List[PotentialNeighborhoodSchema]  # camelCase
    cultureInfo: CultureInfoSchema  # camelCase
    plots: List[PlotResponse]

    model_config = ConfigDict(from_attributes=True)

class NotificationResponse(BaseModel):
    id: str
    message: str
    read: bool
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ChartDayData(BaseModel):
    day: str
    count: int
    active: bool

class DashboardStatsResponse(BaseModel):
    totalViews: int
    totalInquiries: int
    conversionRate: str
    leads: List[InquiryResponse]
    viewsChart: List[ChartDayData]
