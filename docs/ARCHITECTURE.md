# Architecture — Motivational Quote App

> **Living document** — updated automatically by the pipeline after every merged PR.
> Do not edit manually; changes will be overwritten.

## Overview

A Flask web app that takes a user's work description and returns a Claude-generated
motivational quote. Deployed to Azure Container Apps via an AI-driven CI/CD pipeline.

## Components

| Component | Path | Purpose |
|---|---|---|
| Flask application | `app.py` | Main web server — routes, Anthropic client, response rendering |
| HTML template | `templates/index.html` | Jinja2 template — form input + quote display |
| Docker container | `Dockerfile` | Container image definition for Azure deployment |
| Process config | `Procfile` | gunicorn startup command (port 8000) |
| Health endpoint | `app.py:/health` | Returns `{"status": "ok"}` — used by pipeline health checks |

## API Endpoints

| Method | Path | Description | Response |
|---|---|---|---|
| GET | `/` | Render empty quote form | 200 HTML |
| POST | `/` | Submit `work` → generate quote → render result | 200 HTML |
| GET | `/health` | Health check | `{"status": "ok"}` |
| GET | `/ping` | Liveness probe | `{"pong": true}` |
| GET | `/version` | Build info | `{"python_version": "...", "date": "..."}` |

## Data Flow

```
User → POST / (form field: work=<description>)
  │
  ▼
app.py — index() route
  │  strips whitespace from work
  │  if work is non-empty:
  ▼
Anthropic Claude (claude-haiku-4-5-20251001)
  prompt: "Give me a single short, powerful motivational quote
           tailored for someone working on: <work>.
           Reply with just the quote and its author (if known), nothing else."
  │
  ▼
quote = response.content[0].text.strip()
  │
  ▼
render_template("index.html", quote=quote, work=work, error=None)
  │
  ├── <div class="quote-box">{{ quote }}</div>   ← populated on success
  └── <p class="work-label">for: {{ work }}</p>  ← shows submitted input

Error path (Anthropic raises Exception):
  render_template("index.html", error="Could not generate quote: <msg>")
  └── <p class="error">{{ error }}</p>
```

## External Dependencies

| Service | Purpose | Config |
|---|---|---|
| Anthropic API | Quote generation via Claude | `ANTHROPIC_API_KEY` env var |
| Azure Container Registry | Docker image storage | `motivationalquoteacr.azurecr.io` |
| Azure Container Apps | Production + staging hosting | See `deploy.md` |

## Deployment Topology

```
Source (GitHub: manaswinils/agent-sandbox)
  │
  ├─ PR branch ──► AI pipeline (agent-prototype):
  │                  Stage 7:  az acr build → motivationalquoteacr.azurecr.io/motivational-quote-app:<tag>
  │                  Stage 8:  az containerapp update → motivational-quote-app-staging
  │                  Stage 9:  Puppeteer E2E (real Anthropic API, 60s timeout)
  │                  Stage 10: merge_pr (squash to main)
  │                  Stage 11: update living docs → commit to main
  │                  Stage 12: az containerapp update → motivational-quote-app (prod)
  │                  Stage 13: Puppeteer E2E (prod)
  │                            └─ failure: rollback tag + revert main + GitHub issue
  │
  └─ Staging URL:  https://motivational-quote-app-staging.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
     Prod URL:     https://motivational-quote-app.delightfulfield-c939fa9a.eastus.azurecontainerapps.io
```

Both environments run the same Docker image (build once, promote to prod).
Staging has `min-replicas=1` (always on) to eliminate cold-start delays during E2E tests.

## Key Design Constraints

- The Anthropic client `client = Anthropic()` is instantiated once at module level (thread-safe).
- The app does not store any state between requests — fully stateless.
- Port: gunicorn binds to `0.0.0.0:8000`; the Azure Container App ingress targets port 8000.
