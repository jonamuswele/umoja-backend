from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    role: str
    is_approved: bool
    is_suspended: bool

    @staticmethod
    def from_row(row: dict) -> "User":
        return User(
            id=row.get("id"),
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            is_approved=bool(row["is_approved"]),
            is_suspended=bool(row["is_suspended"]),
        )


@dataclass
class Country:
    id: str
    name: str
    flag: str
    motto: Optional[str]
    accent: Optional[str]
    desc: Optional[str]
    video_url: Optional[str]
    highlights: Optional[str]           # JSON string
    potential_neighborhoods: Optional[str]  # JSON string
    culture_info: Optional[str]         # JSON string
    is_visible: bool
    plots: List = field(default_factory=list)

    @staticmethod
    def from_row(row: dict) -> "Country":
        return Country(
            id=row["id"],
            name=row["name"],
            flag=row.get("flag", "🌍"),
            motto=row.get("motto"),
            accent=row.get("accent"),
            desc=row.get("desc"),
            video_url=row.get("video_url"),
            highlights=row.get("highlights"),
            potential_neighborhoods=row.get("potential_neighborhoods"),
            culture_info=row.get("culture_info"),
            is_visible=bool(row.get("is_visible", 1)),
        )


@dataclass
class Plot:
    id: str
    title: str
    size: Optional[str]
    price: float
    neighborhood: Optional[str]
    owner_username: str
    country_id: str
    photos: Optional[str]   # JSON string
    is_visible: bool
    country: Optional[Country] = None

    @staticmethod
    def from_row(row: dict) -> "Plot":
        return Plot(
            id=row["id"],
            title=row["title"],
            size=row.get("size"),
            price=row["price"],
            neighborhood=row.get("neighborhood"),
            owner_username=row["owner_username"],
            country_id=row["country_id"],
            photos=row.get("photos"),
            is_visible=bool(row.get("is_visible", 1)),
        )


@dataclass
class PlotView:
    id: Optional[int]
    plot_id: str
    timestamp: str

    @staticmethod
    def from_row(row: dict) -> "PlotView":
        return PlotView(
            id=row.get("id"),
            plot_id=row["plot_id"],
            timestamp=row["timestamp"],
        )


@dataclass
class Inquiry:
    id: str
    plot_id: str
    full_name: str
    email: str
    phone: Optional[str]
    current_city: Optional[str]
    message: Optional[str]
    type: str
    timestamp: str
    plot_title: Optional[str] = None
    country_name: Optional[str] = None

    @staticmethod
    def from_row(row: dict) -> "Inquiry":
        return Inquiry(
            id=row["id"],
            plot_id=row["plot_id"],
            full_name=row["full_name"],
            email=row["email"],
            phone=row.get("phone"),
            current_city=row.get("current_city"),
            message=row.get("message"),
            type=row["type"],
            timestamp=row["timestamp"],
            plot_title=row.get("plot_title"),
            country_name=row.get("country_name"),
        )


@dataclass
class Notification:
    id: str
    message: str
    read: bool
    timestamp: str

    @staticmethod
    def from_row(row: dict) -> "Notification":
        return Notification(
            id=row["id"],
            message=row["message"],
            read=bool(row.get("read", 0)),
            timestamp=row["timestamp"],
        )
