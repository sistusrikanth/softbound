from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False, index=True)
    summary = Column(Text, default="")
    content = Column(Text, default="")
    category = Column(String(50), default="papers")  # papers, systems, notes
    tags = Column(String(500), default="")
    read_time_min = Column(Integer, default=5)
    featured = Column(Boolean, default=False)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class PhotoLink(Base):
    __tablename__ = "photo_links"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), default="")
    instagram_url = Column(String(1000), nullable=False)
    category = Column(String(50), default="street")  # street, landscape, architecture, portrait
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    url = Column(String(1000), default="")
    status = Column(String(20), default="wip")  # live, wip
    tech_tags = Column(String(500), default="")
    icon_color = Column(String(20), default="#6366f1")
    sort_order = Column(Integer, default=0)


class StartupIdea(Base):
    __tablename__ = "startup_ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    contact_url = Column(String(1000), default="")
    sort_order = Column(Integer, default=0)


class DayEntry(Base):
    __tablename__ = "day_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD
    personal = Column(Text, default="")
    professional = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WeekSummary(Base):
    __tablename__ = "week_summaries"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(String(10), unique=True, nullable=False, index=True)  # Monday YYYY-MM-DD
    summary = Column(Text, default="")
    is_complete = Column(Boolean, default=False)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String(300), nullable=False)
    degree = Column(String(300), default="")
    field = Column(String(300), default="")
    start_year = Column(String(10), default="")
    end_year = Column(String(10), default="")
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)


class WorkExperience(Base):
    __tablename__ = "work_experience"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(300), nullable=False)
    role = Column(String(300), nullable=False)
    location = Column(String(200), default="")
    start_date = Column(String(20), default="")
    end_date = Column(String(20), default="")
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)


class ExperienceProject(Base):
    __tablename__ = "experience_projects"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    summary = Column(Text, default="")
    role_context = Column(String(300), default="")
    ml_components = Column(Text, default="[]")  # JSON array
    technical_detail = Column(Text, default="")
    sort_order = Column(Integer, default=0)


class IdentityCard(Base):
    __tablename__ = "identity_cards"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(Text, default="")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
