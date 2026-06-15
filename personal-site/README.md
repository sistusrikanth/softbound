# Lattice Portfolio

A personal portfolio and writing site — dark, minimal, grid-based. Built to match the Lattice design system.

**Live sections:** Index · Writing · Systems · Photography · Projects · Admin

## Stack

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + SQLite
- **Hosting:** Google Cloud Run (free tier eligible)

## Quick start (local)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env    # edit ADMIN_PASSWORD
cd ..
DATA_DIR=./data uvicorn backend.main:app --reload --port 8080
```

### 2. Frontend (dev server with API proxy)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5175](http://localhost:5175). Admin panel: [http://localhost:5175/admin](http://localhost:5175/admin)

Default admin password: `admin123` (change via `ADMIN_PASSWORD` in `.env`)

## Admin panel

Go to `/admin` to sign in and:

- **Write articles** in Markdown (papers, systems, notes)
- **Add Instagram photo links** with categories (street, landscape, architecture, portrait)
- **Day tracker** at `/private/days` — log personal and professional accomplishments each day
- **Who I am** at `/private/identity` — a few lines per category reminding you who you are and the face of each site section

Private pages use the same admin password and are not linked from the public navigation.

Articles are stored in SQLite at `data/site.db`.

## Production build

```bash
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt
DATA_DIR=../data uvicorn main:app --port 8080
```

The Vite build outputs to `backend/static/` and FastAPI serves it as a SPA.

## Deploy to GCP Cloud Run (free tier)

Cloud Run's always-free tier includes **2 million requests/month** — more than enough for a personal site.

### One-time GCP setup

```bash
# Install gcloud CLI, then:
gcloud auth login
gcloud projects create YOUR_PROJECT_ID --name="Lattice Portfolio"
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry repo
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker --location=us-central1

# Build and deploy
cd personal-site
gcloud run deploy lattice-portfolio \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "ADMIN_PASSWORD=your-secure-password,ADMIN_SECRET_KEY=$(openssl rand -hex 16),SITE_NAME=kiran rao"
```

Your site will be live at `https://lattice-portfolio-XXXXX-uc.a.run.app`

### CI/CD with GitHub Actions

1. Set up [Workload Identity Federation](https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions) for keyless deploys
2. Add GitHub secrets: `GCP_PROJECT_ID`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `ADMIN_PASSWORD`, `ADMIN_SECRET_KEY`
3. Push to `main` — the workflow in `.github/workflows/deploy.yml` deploys automatically

### Data persistence

Cloud Run containers are ephemeral. For production:

- Mount a [Cloud Storage volume](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts) at `/data` to persist SQLite
- Or back up `data/site.db` periodically

## Customize

Set environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `SITE_NAME` | Your name in the header |
| `SITE_TAGLINE` | Footer tagline |
| `SITE_LOCATION` | City shown on index page |
| `SITE_GITHUB` | GitHub profile URL |
| `SITE_EMAIL` | Contact email |
| `ADMIN_PASSWORD` | Admin panel password |
| `ADMIN_SECRET_KEY` | JWT signing key (random string) |

## Project structure

```
personal-site/
├── frontend/          # React SPA
├── backend/           # FastAPI API + static file serving
├── data/              # SQLite database (gitignored)
├── Dockerfile         # Production container
└── .github/workflows/ # CI/CD
```
