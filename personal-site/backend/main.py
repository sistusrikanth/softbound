import json
import os
import re
import unicodedata
import uuid
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from auth import create_access_token, require_admin, verify_password
from database import DATA_DIR, Base, SessionLocal, engine, get_db
from models import (
    Article,
    DayEntry,
    Education,
    ExperienceProject,
    IdentityCard,
    PhotoLink,
    Project,
    StartupIdea,
    WeekSummary,
    WorkExperience,
)
from schemas import (
    ArticleCreate,
    ArticleOut,
    ArticleUpdate,
    DayEntryCreate,
    DayEntryOut,
    EducationOut,
    ExperienceOut,
    ExperienceProjectDetailOut,
    ExperienceProjectOut,
    IdentityCardOut,
    IdentityCardUpdate,
    LoginRequest,
    MLComponent,
    PhotoLinkCreate,
    PhotoLinkOut,
    ProjectOut,
    StartupIdeaOut,
    Token,
    UploadOut,
    WeekDayOut,
    WeekSummaryOut,
    WeekSummaryUpdate,
    WorkExperienceOut,
)

STATIC_DIR = Path(__file__).parent / "static"
UPLOADS_DIR = Path(DATA_DIR) / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
ALLOWED_EXCALIDRAW_EXT = {".excalidraw"}
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_start_for(entry_date: str) -> str:
    return monday_of(date.fromisoformat(entry_date)).isoformat()


def week_dates(week_start: str) -> list[str]:
    start = date.fromisoformat(week_start)
    return [(start + timedelta(days=i)).isoformat() for i in range(7)]


def week_end_for(week_start: str) -> str:
    return week_dates(week_start)[6]


def _entry_has_content(entry: DayEntry | None) -> bool:
    if not entry:
        return False
    return bool(entry.personal.strip() or entry.professional.strip())


def _build_week_summary(week_start: str, entries: dict[str, DayEntry]) -> str:
    start = date.fromisoformat(week_start)
    end = date.fromisoformat(week_end_for(week_start))
    header = f"Week of {start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
    personal_lines: list[str] = []
    professional_lines: list[str] = []

    for day_iso in week_dates(week_start):
        entry = entries.get(day_iso)
        if not entry:
            continue
        label = date.fromisoformat(day_iso).strftime("%A")
        if entry.personal.strip():
            personal_lines.append(f"- **{label}:** {entry.personal.strip()}")
        if entry.professional.strip():
            professional_lines.append(f"- **{label}:** {entry.professional.strip()}")

    parts = [header]
    if personal_lines:
        parts.append("\n**Personal**\n" + "\n".join(personal_lines))
    if professional_lines:
        parts.append("\n**Professional**\n" + "\n".join(professional_lines))
    return "\n".join(parts)


def _refresh_week_summary(db: Session, entry_date: str) -> None:
    week_start = week_start_for(entry_date)
    dates = week_dates(week_start)
    entries_list = db.query(DayEntry).filter(DayEntry.entry_date.in_(dates)).all()
    entries = {e.entry_date: e for e in entries_list}
    filled_count = sum(1 for d in dates if _entry_has_content(entries.get(d)))
    is_complete = filled_count == 7

    summary_row = db.query(WeekSummary).filter(WeekSummary.week_start == week_start).first()
    if is_complete:
        generated = _build_week_summary(week_start, entries)
        if summary_row:
            if not summary_row.is_custom:
                summary_row.summary = generated
            summary_row.is_complete = True
        else:
            db.add(WeekSummary(week_start=week_start, summary=generated, is_complete=True))
    elif summary_row:
        summary_row.is_complete = False
    db.commit()


def _week_summary_out(db: Session, week_start: str) -> WeekSummaryOut:
    dates = week_dates(week_start)
    entries_list = db.query(DayEntry).filter(DayEntry.entry_date.in_(dates)).all()
    entries = {e.entry_date: e for e in entries_list}
    filled_count = sum(1 for d in dates if _entry_has_content(entries.get(d)))
    summary_row = db.query(WeekSummary).filter(WeekSummary.week_start == week_start).first()

    days = []
    for day_iso in dates:
        entry = entries.get(day_iso)
        days.append(
            WeekDayOut(
                entry_date=day_iso,
                personal=entry.personal if entry else "",
                professional=entry.professional if entry else "",
                has_entry=_entry_has_content(entry),
            )
        )

    return WeekSummaryOut(
        week_start=week_start,
        week_end=week_end_for(week_start),
        days=days,
        filled_count=filled_count,
        is_complete=filled_count == 7,
        summary=summary_row.summary if summary_row else "",
    )


def seed_data(db: Session):
    if db.query(Article).count() > 0:
        return

    articles = [
        Article(
            title="Attention is a weighted lookup",
            slug="attention-is-a-weighted-lookup",
            summary="Transformers reduce to one operation: weighted retrieval over a key-value store. Everything else is bookkeeping.",
            content="""# Attention is a weighted lookup

Transformers look complicated until you strip away the notation. At the core, **attention is just a weighted lookup** over a key-value store.

## The setup

You have three matrices: **Q** (queries), **K** (keys), and **V** (values). For each query vector, you:

1. Compute similarity scores against every key
2. Softmax those scores into weights
3. Return a weighted sum of value vectors

That's it. The rest — multi-head attention, positional encodings, layer norms — is engineering around this primitive.

## Why it works

Language is full of long-range dependencies. A pronoun ten words back needs to bind to a noun. Attention gives every token direct access to every other token in one hop, instead of squeezing context through a fixed-size bottleneck.

## The cost

Quadratic memory in sequence length. At 8k tokens you're fine. At 128k you need KV-cache tricks, sparse patterns, or ring attention.

---

*This is a seed article. Edit or replace it from the admin panel.*
""",
            category="papers",
            tags="transformers",
            read_time_min=14,
            featured=True,
        ),
        Article(
            title="Designing a feature store",
            slug="designing-a-feature-store",
            summary="Online vs offline features, point-in-time correctness, and why most teams get the serving path wrong.",
            content="# Designing a feature store\n\nSeed content — replace from admin.",
            category="systems",
            tags="data,serving",
            read_time_min=11,
        ),
        Article(
            title="KV-cache eviction heuristics",
            slug="kv-cache-eviction",
            summary="Quick notes on what to drop when context windows outgrow GPU memory.",
            content="# KV-cache eviction\n\nSeed content — replace from admin.",
            category="notes",
            tags="gpu,inference",
            read_time_min=6,
        ),
    ]
    db.add_all(articles)

    photos = [
        PhotoLink(title="Lisbon morning", instagram_url="https://www.instagram.com/", category="street", sort_order=1),
        PhotoLink(title="Coast light", instagram_url="https://www.instagram.com/", category="landscape", sort_order=2),
        PhotoLink(title="Concrete curves", instagram_url="https://www.instagram.com/", category="architecture", sort_order=3),
    ]
    db.add_all(photos)

    projects = [
        Project(
            title="lattice",
            description="A personal publishing system — writing, systems, photography in one grid.",
            url="#",
            status="live",
            tech_tags="ts,react,python",
            icon_color="#6366f1",
            sort_order=1,
        ),
        Project(
            title="ring-buffer",
            description="Zero-copy ring buffer for streaming inference pipelines.",
            url="#",
            status="wip",
            tech_tags="rust,wasm",
            icon_color="#8b5cf6",
            sort_order=2,
        ),
        Project(
            title="paper-lens",
            description="Upload a PDF, get a component diagram and a plain-English walkthrough.",
            url="#",
            status="wip",
            tech_tags="python,pdf.js",
            icon_color="#3b82f6",
            sort_order=3,
        ),
    ]
    db.add_all(projects)

    ideas = [
        StartupIdea(
            title="Diff for ML configs",
            description="Git-style diffs for training configs — see exactly what changed between runs and why loss moved.",
            contact_url="mailto:hello@example.com",
            sort_order=1,
        ),
        StartupIdea(
            title="On-call for models",
            description="PagerDuty, but the alerts are drift scores and latency regressions, not disk space.",
            contact_url="mailto:hello@example.com",
            sort_order=2,
        ),
        StartupIdea(
            title="Notebook CI",
            description="Run notebooks as tests on every PR. Catch stale outputs before they ship.",
            contact_url="mailto:hello@example.com",
            sort_order=3,
        ),
    ]
    db.add_all(ideas)
    db.commit()


def _seed_identity(db: Session):
    if db.query(IdentityCard).count() > 0:
        return
    identity_seed = [
        ("who_i_am", "I break complex systems down to their essence. Reader, builder, photographer — based in Lisbon."),
        ("what_i_do", "I read research papers and rebuild them from first principles. I design ML systems in the open. I shoot cities and light between commits."),
        ("what_i_care_about", "Clarity over cleverness. Systems that survive failure. Ideas that outlive the hype cycle. Showing up every day."),
        ("writing", "Research papers, taken apart and rebuilt from their core components — the wiring made visible."),
        ("systems", "The ML systems everyone leans on, drawn out from first principles — trade-offs left in."),
        ("photography", "A working portfolio. Film when there's time, digital when there isn't."),
        ("projects", "Things I'm building and startup ideas I can't stop thinking about."),
    ]
    for category, content in identity_seed:
        db.add(IdentityCard(category=category, content=content))
    db.commit()


def _seed_experience(db: Session):
    if db.query(Education).count() > 0:
        return

    db.add_all([
        Education(
            institution="University",
            degree="M.S.",
            field="Computer Science / Machine Learning",
            start_year="2018",
            end_year="2020",
            description="Focused on distributed systems, deep learning, and probabilistic modeling.",
            sort_order=1,
        ),
        Education(
            institution="University",
            degree="B.Tech",
            field="Computer Science",
            start_year="2014",
            end_year="2018",
            description="Core coursework in algorithms, systems, and applied mathematics.",
            sort_order=2,
        ),
    ])

    db.add_all([
        WorkExperience(
            company="ML Platform Team",
            role="Senior ML Engineer",
            location="Remote",
            start_date="2022",
            end_date="Present",
            description="Own inference pipelines, model serving, and observability for production ML systems.",
            sort_order=1,
        ),
        WorkExperience(
            company="Applied AI Lab",
            role="ML Engineer",
            location="San Francisco, CA",
            start_date="2020",
            end_date="2022",
            description="Built retrieval-augmented generation stacks and evaluation harnesses for research-to-production handoffs.",
            sort_order=2,
        ),
    ])

    rag_components = json.dumps([
        {
            "name": "Hybrid retriever",
            "description": "Combines dense embeddings with sparse lexical signals for recall under domain shift.",
            "technical_aspects": [
                "FAISS IVF index with 768-d embeddings",
                "BM25 reranking pass on top-200 candidates",
                "Cross-encoder rescoring for final top-8 context window",
            ],
        },
        {
            "name": "Generation stack",
            "description": "Latency-bounded LLM serving with structured citation outputs.",
            "technical_aspects": [
                "vLLM batching with p95 < 800ms",
                "JSON schema constrained decoding for citations",
                "KV-cache reuse across multi-turn sessions",
            ],
        },
        {
            "name": "Evaluation loop",
            "description": "Offline + online metrics tying retrieval quality to downstream answer faithfulness.",
            "technical_aspects": [
                "nDCG@10 on golden query sets",
                "LLM-as-judge with human calibration set",
                "Drift alerts on embedding centroid shift",
            ],
        },
    ])

    serving_components = json.dumps([
        {
            "name": "Model router",
            "description": "Routes requests to GPU pools based on model size, SLA tier, and queue depth.",
            "technical_aspects": [
                "Weighted round-robin with circuit breakers",
                "Cold-start mitigation via warm replica pools",
                "Per-tenant rate limits and quota tracking",
            ],
        },
        {
            "name": "Feature store integration",
            "description": "Online features for real-time inference with point-in-time correctness.",
            "technical_aspects": [
                "Redis-backed low-latency feature lookups",
                "Feast offline/online sync with versioned schemas",
                "Backfill jobs for training-serving skew detection",
            ],
        },
    ])

    db.add_all([
        ExperienceProject(
            slug="rag-platform",
            title="Production RAG Platform",
            summary="End-to-end retrieval-augmented generation for internal knowledge search at scale.",
            role_context="Senior ML Engineer · ML Platform Team",
            ml_components=rag_components,
            technical_detail="""## Overview

Designed and shipped a retrieval-augmented generation platform serving thousands of daily queries across internal documentation, runbooks, and design docs.

## Architecture

The system splits into three layers: ingestion (chunking + embedding), retrieval (hybrid search + reranking), and generation (constrained LLM output with citations).

## Outcomes

- Cut median time-to-answer for support engineers by ~40%
- Reduced hallucination rate on eval set from 18% to 6%
- Established a weekly eval cadence tied to deploy gates
""",
            sort_order=1,
        ),
        ExperienceProject(
            slug="model-serving-mesh",
            title="Model Serving Mesh",
            summary="Multi-tenant GPU inference mesh with routing, autoscaling, and observability.",
            role_context="ML Engineer · Applied AI Lab",
            ml_components=serving_components,
            technical_detail="""## Overview

Built a serving layer that let multiple product teams deploy ONNX and PyTorch models without owning GPU infrastructure.

## Key decisions

- Sidecar pattern for model versioning vs. blue/green at the router
- Prometheus + custom latency histograms per model revision
- Shadow traffic for canary validation before promotion

## Outcomes

- Onboarding time for new models dropped from weeks to days
- p99 latency held under 250ms for 95% of models at peak load
""",
            sort_order=2,
        ),
    ])
    db.commit()


def _migrate_schema() -> None:
    migrations = [
        "ALTER TABLE week_summaries ADD COLUMN is_custom BOOLEAN DEFAULT 0",
    ]
    with engine.begin() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    db = SessionLocal()
    try:
        seed_data(db)
        _seed_identity(db)
        _seed_experience(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Lattice Portfolio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth ---

@app.post("/api/auth/login", response_model=Token)
def login(body: LoginRequest):
    if not verify_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return Token(access_token=create_access_token())


# --- Articles (public) ---

@app.get("/api/articles", response_model=list[ArticleOut])
def list_articles(
    category: str | None = None,
    featured: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Article).filter(Article.published == True)
    if category and category != "all":
        q = q.filter(Article.category == category)
    if featured is not None:
        q = q.filter(Article.featured == featured)
    return q.order_by(Article.created_at.desc()).all()


@app.get("/api/articles/{slug}", response_model=ArticleOut)
def get_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug, Article.published == True).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


# --- Articles (admin) ---

@app.post("/api/admin/articles", response_model=ArticleOut)
def create_article(body: ArticleCreate, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    slug = body.slug or slugify(body.title)
    if db.query(Article).filter(Article.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    article = Article(**body.model_dump(exclude={"slug"}), slug=slug)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@app.put("/api/admin/articles/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: int,
    body: ArticleUpdate,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        if key == "slug" and value:
            existing = db.query(Article).filter(Article.slug == value, Article.id != article_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Slug already exists")
        setattr(article, key, value)
    db.commit()
    db.refresh(article)
    return article


@app.delete("/api/admin/articles/{article_id}")
def delete_article(article_id: int, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"ok": True}


@app.get("/api/admin/articles", response_model=list[ArticleOut])
def admin_list_articles(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.created_at.desc()).all()


# --- Uploads (admin) ---

@app.post("/api/admin/uploads", response_model=UploadOut)
async def upload_attachment(
    file: UploadFile = File(...),
    _: bool = Depends(require_admin),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = Path(file.filename).suffix.lower()
    if ext in ALLOWED_IMAGE_EXT:
        kind = "image"
    elif ext in ALLOWED_EXCALIDRAW_EXT:
        kind = "excalidraw"
    else:
        raise HTTPException(
            status_code=400,
            detail="Allowed: images (png, jpg, gif, webp, svg) or .excalidraw files",
        )

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 12 MB)")

    if kind == "excalidraw":
        try:
            json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid Excalidraw file")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / stored_name
    dest.write_bytes(data)

    return UploadOut(url=f"/uploads/{stored_name}", filename=file.filename, kind=kind)


# --- Photography ---

@app.get("/api/photos", response_model=list[PhotoLinkOut])
def list_photos(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PhotoLink)
    if category and category != "all":
        q = q.filter(PhotoLink.category == category)
    return q.order_by(PhotoLink.sort_order, PhotoLink.created_at.desc()).all()


@app.post("/api/admin/photos", response_model=PhotoLinkOut)
def create_photo(body: PhotoLinkCreate, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    photo = PhotoLink(**body.model_dump())
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@app.delete("/api/admin/photos/{photo_id}")
def delete_photo(photo_id: int, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    photo = db.query(PhotoLink).filter(PhotoLink.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(photo)
    db.commit()
    return {"ok": True}


# --- Projects ---

@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.sort_order).all()


@app.get("/api/ideas", response_model=list[StartupIdeaOut])
def list_ideas(db: Session = Depends(get_db)):
    return db.query(StartupIdea).order_by(StartupIdea.sort_order).all()


# --- Private: day tracker (admin only) ---

@app.get("/api/admin/days", response_model=list[DayEntryOut])
def list_day_entries(
    limit: int = Query(60, le=365),
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(DayEntry).order_by(DayEntry.entry_date.desc()).limit(limit).all()


@app.get("/api/admin/days/{entry_date}", response_model=DayEntryOut)
def get_day_entry(entry_date: str, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.query(DayEntry).filter(DayEntry.entry_date == entry_date).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@app.put("/api/admin/days/{entry_date}", response_model=DayEntryOut)
def upsert_day_entry(
    entry_date: str,
    body: DayEntryCreate,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entry = db.query(DayEntry).filter(DayEntry.entry_date == entry_date).first()
    if entry:
        entry.personal = body.personal
        entry.professional = body.professional
    else:
        entry = DayEntry(entry_date=entry_date, personal=body.personal, professional=body.professional)
        db.add(entry)
    db.commit()
    db.refresh(entry)
    _refresh_week_summary(db, entry_date)
    return entry


@app.delete("/api/admin/days/{entry_date}")
def delete_day_entry(entry_date: str, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.query(DayEntry).filter(DayEntry.entry_date == entry_date).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    _refresh_week_summary(db, entry_date)
    return {"ok": True}


@app.get("/api/admin/weeks/{week_start}", response_model=WeekSummaryOut)
def get_week_summary(week_start: str, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        date.fromisoformat(week_start)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid week_start")
    return _week_summary_out(db, week_start)


@app.put("/api/admin/weeks/{week_start}/summary", response_model=WeekSummaryOut)
def update_week_summary(
    week_start: str,
    body: WeekSummaryUpdate,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    summary_row = db.query(WeekSummary).filter(WeekSummary.week_start == week_start).first()
    if summary_row:
        summary_row.summary = body.summary
        summary_row.is_custom = True
    else:
        db.add(WeekSummary(week_start=week_start, summary=body.summary, is_custom=True))
    db.commit()
    return _week_summary_out(db, week_start)


# --- Experience (public) ---

@app.get("/api/experience", response_model=ExperienceOut)
def get_experience(db: Session = Depends(get_db)):
    return ExperienceOut(
        education=db.query(Education).order_by(Education.sort_order).all(),
        work=db.query(WorkExperience).order_by(WorkExperience.sort_order).all(),
        projects=db.query(ExperienceProject).order_by(ExperienceProject.sort_order).all(),
    )


@app.get("/api/experience/projects/{slug}", response_model=ExperienceProjectDetailOut)
def get_experience_project(slug: str, db: Session = Depends(get_db)):
    project = db.query(ExperienceProject).filter(ExperienceProject.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        components = [MLComponent(**c) for c in json.loads(project.ml_components or "[]")]
    except (json.JSONDecodeError, TypeError, ValueError):
        components = []
    return ExperienceProjectDetailOut(
        id=project.id,
        slug=project.slug,
        title=project.title,
        summary=project.summary,
        role_context=project.role_context,
        sort_order=project.sort_order,
        ml_components=components,
        technical_detail=project.technical_detail,
    )


# --- Private: identity cards (admin only) ---

IDENTITY_ORDER = [
    "who_i_am", "what_i_do", "what_i_care_about",
    "writing", "systems", "photography", "projects",
]


@app.get("/api/admin/identity", response_model=list[IdentityCardOut])
def list_identity_cards(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    cards = db.query(IdentityCard).all()
    order = {cat: i for i, cat in enumerate(IDENTITY_ORDER)}
    return sorted(cards, key=lambda c: order.get(c.category, 99))


@app.put("/api/admin/identity/{category}", response_model=IdentityCardOut)
def update_identity_card(
    category: str,
    body: IdentityCardUpdate,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    card = db.query(IdentityCard).filter(IdentityCard.category == category).first()
    if not card:
        card = IdentityCard(category=category, content=body.content)
        db.add(card)
    else:
        card.content = body.content
    db.commit()
    db.refresh(card)
    return card


# --- Site config ---

@app.get("/api/config")
def site_config():
    return {
        "name": os.environ.get("SITE_NAME", "srikanth sistu"),
        "tagline": os.environ.get("SITE_TAGLINE", "writing, systems & photography"),
        "location": os.environ.get("SITE_LOCATION", "Lisbon"),
        "github": os.environ.get("SITE_GITHUB", "https://github.com/sistusrikanth"),
        "twitter": os.environ.get("SITE_TWITTER", ""),
        "email": os.environ.get("SITE_EMAIL", ""),
        "now_text": os.environ.get(
            "SITE_NOW_TEXT",
            "Writing up a piece on KV-cache eviction. Shooting a roll of Portra in Lisbon.",
        ),
    }


# --- Static files (production) ---

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
