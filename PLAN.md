# Food Picker Web App — Implementation Plan

## Context

The food-picker project is a Python stub with a `choices.md` seed file. The goal is an **API-first** web service: a JSON REST API usable directly from curl, plus a mobile-optimized browser frontend that calls the same API. `choices.md` is used only as the seed for `places.toml` at project setup — no ongoing support for that format is needed.

---

## Architecture: API-First

```
                  Browser (mobile web app)
                         │ fetch()
                  ┌──────▼──────┐
curl ────────────►│  Flask API  │◄── uv run flask / gunicorn
                  │  /api/*     │
                  └──────┬──────┘
                         │ atomic read/write
                    places.toml  (bind-mounted)
```

The Flask app has two blueprints:
- **`/api/`** — JSON REST API (orjson responses). All business logic lives here.
- **`/`** — Serves the static SPA shell (one HTML file + JS + CSS). The SPA calls the API.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.14 | Already pinned |
| Framework | **Flask 3.x** | Lightweight; two blueprints (API + static SPA) |
| Data models | **Pydantic v2** | Type-safe, validates on load and on API input |
| Data format | **TOML** (`places.toml`) | Human-friendly for hand-editing if needed |
| TOML read | `tomllib` (stdlib) | No extra dep for reading |
| TOML write | `tomli-w` | Lightweight pure-Python TOML serializer |
| JSON | **orjson** | Fast JSON; used for all API responses |
| Frontend | **Vanilla JS + Pico CSS** | Minimal, mobile-optimized; no build step |
| Reverse proxy | **Caddy 2** | Auto Let's Encrypt with a 2-line Caddyfile |
| WSGI server | **Gunicorn** | Multi-worker, pure Python |
| Package manager | **uv** | Fast, reproducible dependency management |

---

## Data Structure

### `places.toml` (primary data store, bind-mounted in Docker)

```toml
categories = ["Fast Food", "Quality Nommings", "Fancy Fixings"]

[[places]]
name = "McDonalds"
categories = ["Fast Food"]

[[places]]
name = "Five Guys"
categories = ["Fast Food", "Quality Nommings"]
```

- A place can belong to **one or more categories** (many-to-many).
- The top-level `categories` list is authoritative for ordering and which categories exist.
- `choices.md` is converted to this format once at project setup (see below).

### Pydantic Models (`app/models.py`)

```python
class Place(BaseModel):
    name: str
    categories: list[str]

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("categories")
    @classmethod
    def at_least_one_category(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("place must have at least one category")
        return v

class PlacesData(BaseModel):
    categories: list[str]
    places: list[Place]
```

API route handlers accept Pydantic models as input (parsed from request JSON). `ValidationError` is caught and returned as a 422 response.

---

## API Endpoints

All under `/api/`, all return JSON via orjson.

### Pick

```
GET /api/pick
  ?categories=Fast+Food&categories=Quality+Nommings
  &vetoed=McDonalds&vetoed=Wendy%27s
```
Returns `{"name": "Whataburger"}` or `{"error": "no options remaining"}` (HTTP 409).

curl example:
```bash
curl "https://yourdomain.com/api/pick?categories=Fast+Food"
curl "https://yourdomain.com/api/pick"   # all categories
```

### Places

```
GET    /api/places                  → list of all places with categories
POST   /api/places                  → add place {name, categories}
DELETE /api/places/<name>           → delete place by name
PUT    /api/places/<name>           → update place {name?, categories?}
```

### Categories

```
GET    /api/categories              → ordered list of category names
POST   /api/categories              → add category {name}
DELETE /api/categories/<name>       → remove category (strips from all places)
PUT    /api/categories              → reorder categories {categories: [...]}
```

### Import / Export

```
GET  /api/export?format=toml        → download places.toml (Content-Disposition: attachment)
GET  /api/export?format=json        → download places as JSON
POST /api/import                    → multipart file upload (TOML or JSON); replaces all data
```

Export formats:
- **TOML**: the native `places.toml` format
- **JSON**: `{"categories": [...], "places": [{name, categories}, ...]}`

Import accepts either format (auto-detected by file extension or Content-Type). On import, the uploaded data is validated via `PlacesData` before writing, so a bad file returns 422 without touching the current data.

---

## Directory Structure

```
food-picker/
├── choices.md                        # seed data only — converted once at setup
├── places.toml                       # primary data store (bind-mounted in Docker)
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── .env.example
├── README.md                         # human-useful: setup, usage, API reference, deployment
├── PLAN.md                           # this planning document (implementation roadmap)
├── .claude/
│   └── settings.json                 # PostToolUse hooks
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # ruff + ty + bandit + pytest on push/PR
│   │   └── release.yml               # build + push Docker image to GHCR on v* tag
│   └── dependabot.yml                # weekly dep bumps
├── CLAUDE.md                         # project context for Claude Code
├── tests/
│   ├── conftest.py
│   ├── test_data.py
│   ├── test_api_pick.py
│   ├── test_api_places.py
│   ├── test_api_categories.py
│   └── test_api_import_export.py
└── app/
    ├── __init__.py                   # Flask app factory
    ├── models.py                     # Pydantic: Place, PlacesData
    ├── data.py                       # load/save places.toml, import/export logic
    ├── api/
    │   ├── __init__.py
    │   └── routes.py                 # all /api/* endpoints
    ├── web/
    │   ├── __init__.py
    │   └── routes.py                 # GET / → serve SPA shell
    └── static/
        ├── index.html                # SPA shell
        ├── app.js                    # all frontend logic (fetch calls to /api/*)
        └── style.css                 # mobile-optimized styles (or Pico CSS CDN)
```

---

## Data Layer (`app/data.py`)

**`load_places(path) -> PlacesData`**: `tomllib.loads(path.read_bytes())` → `PlacesData.model_validate(...)`. Raises on parse or validation error.

**`save_places(path, data: PlacesData)`**: `data.model_dump()` → `tomli_w.dumps(...)` → write to `.tmp` sibling → `os.replace(tmp, path)`. Atomic on POSIX.

**`export_json(data: PlacesData) -> bytes`**: `orjson.dumps(data.model_dump(), option=orjson.OPT_INDENT_2)`.

**`import_data(raw: bytes, fmt: str) -> PlacesData`**: Parse TOML or JSON, validate via `PlacesData.model_validate()`, return without writing (caller decides whether to save).

**One-time seed**: A CLI helper (or a check in `load_places`) converts `choices.md` to `places.toml` on first run if `places.toml` doesn't exist. This runs at `uv run python -m app.seed` or automatically on startup.

---

## Frontend (SPA)

- **`index.html`**: Minimal shell — loads Pico CSS from CDN, loads `app.js`, has a `<main>` container.
- **`app.js`**: Vanilla JS. On load: `GET /api/categories` + `GET /api/places` to populate the UI. No frameworks, no build step, no TypeScript (keeps it simple for a family tool).

**Home view** (mobile-first layout):
1. Category toggles (tappable chips, not tiny checkboxes)
2. "Pick for me" button → `GET /api/pick?categories=...`
3. Result card: restaurant name, "Veto" button, "That's it!" button
4. Veto: re-calls `GET /api/pick?categories=...&vetoed=...&vetoed=...`

**Manage view**:
1. List of places with category tags; tap to edit, swipe/button to delete
2. "Add place" form
3. Category management section

---

## Docker Compose

```yaml
services:
  app:
    build: .
    restart: unless-stopped
    volumes:
      - ./places.toml:/app/places.toml
    environment:
      - PLACES_FILE=/app/places.toml
    expose:
      - "8000"

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
```

---

## Caddyfile

```
{$DOMAIN} {
    reverse_proxy app:8000
}
```

Default hostname is `eat.starfleet.top` (set in `.env`). The `{$DOMAIN}` env var substitution means any hostname works — override by changing `.env` before `docker compose up`.

**.env.example**:
```
DOMAIN=eat.starfleet.top
PLACES_FILE=/app/places.toml
```

---

## Dockerfile

```dockerfile
FROM python:3.14-slim
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/
# places.toml comes from the bind mount at runtime
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:create_app()"]
```

---

## pyproject.toml Dependencies

```toml
[project]
dependencies = [
    "flask>=3.0",
    "gunicorn>=22.0",
    "pydantic>=2.0",
    "orjson>=3.0",
    "tomli-w>=1.0",
]

[tool.uv]
dev-dependencies = [
    "ruff>=0.9",
    "ty>=0.0.1a0",
    "bandit>=1.9",
    "pre-commit>=4.0",
    "pytest>=8.0",
    "pytest-cov>=6.0",
]
```

---

## Tests (`tests/`)

```
tests/
├── conftest.py          # Flask test client fixture, tmp places.toml fixture
├── test_data.py         # load_places, save_places, import_data, export_json
├── test_api_pick.py     # GET /api/pick — category filtering, veto accumulation, pool exhaustion
├── test_api_places.py   # CRUD: add, delete, update places
├── test_api_categories.py  # CRUD: add, delete, reorder categories
└── test_api_import_export.py  # round-trip TOML and JSON import/export
```

**Coverage config** in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
omit = ["app/seed.py"]   # one-time migration script; not worth testing

[tool.coverage.report]
show_missing = true
```

Run tests:
```bash
uv run pytest
```

Key test cases:
- `test_data.py`: atomic write survives concurrent-read scenario; bad TOML raises; Pydantic validation rejects empty name and empty categories list
- `test_api_pick.py`: returns 409 when all places vetoed; respects `categories` filter; never returns a vetoed name; works with no `categories` param (picks from all)
- `test_api_import_export.py`: export TOML → re-import → data unchanged (round-trip); import with invalid TOML returns 422 without modifying data

---

## Config Files (already present — do not recreate)

- **`.ruff.toml`** — line length 100, double quotes, LF endings, full lint rule set (E/F/W/B/C4/I/N/etc.)
- **`.bandit.yml`** — skips B101 (assert) and B113 (timeout); excludes tests/docs/migrations
- **`.pre-commit-config.yaml`** — runs trailing-whitespace, end-of-file-fixer, check-yaml, ruff (with `--config=.ruff.toml`), ruff-format, and bandit

Pre-commit runs on `git commit`. To install the hooks after `uv sync`:
```bash
uv run pre-commit install
```

---

## Claude Hooks

**File**: `.claude/settings.json`

Four `PostToolUse` hooks triggered after `Edit` or `Write`:

### 1. Python files → ruff + ty + bandit
After any `.py` edit: format, lint-fix, typecheck, and SAST scan.
```
ruff format --config=.ruff.toml <file>
ruff check --fix --config=.ruff.toml <file>
ty check          # project-wide; ty doesn't accept single-file targets
bandit -c .bandit.yml <file>
```

### 2. TOML files → syntax validation
After any `.toml` edit (including `pyproject.toml`, `places.toml`, `Caddyfile` if using TOML format):
```
python3 -c "import tomllib; tomllib.load(open('<file>', 'rb'))"
```
Catches broken TOML before it causes cryptic runtime errors.

If the file edited is `pyproject.toml`, also run:
```
uv lock
```
Keeps `uv.lock` in sync whenever dependencies change.

### 3. YAML files → syntax validation
After any `.yaml`/`.yml` edit (including `.pre-commit-config.yaml`, `.bandit.yml`):
```
python3 -c "import yaml; yaml.safe_load(open('<file>'))"
```

### 4. docker-compose.yml → config validation
After editing `docker-compose.yml`:
```
docker compose config
```
Validates compose schema and environment variable substitution.

---

Full `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "cd /Users/ubahmapk/github/food-picker && file=$(echo \"$CLAUDE_TOOL_INPUT\" | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))\") && if [[ \"$file\" == *.py ]]; then uv run ruff format --config=.ruff.toml \"$file\" && uv run ruff check --fix --config=.ruff.toml \"$file\" && uv run ty check && uv run bandit -c .bandit.yml \"$file\"; elif [[ \"$file\" == *.toml ]]; then python3 -c \"import tomllib; tomllib.load(open('$file','rb'))\" && { [[ \"$file\" == *pyproject.toml ]] && uv lock || true; }; elif [[ \"$file\" == *.yaml || \"$file\" == *.yml ]]; then python3 -c \"import yaml; yaml.safe_load(open('$file'))\"; elif [[ \"$file\" == *docker-compose.yml ]]; then docker compose config > /dev/null; fi"
          }
        ]
      }
    ]
  }
}
```

---

## Project Documentation

### `README.md`

Human-useful reference covering:
- **What it is**: one-paragraph description
- **Quick start**: `uv sync`, seed `places.toml`, run dev server
- **API reference**: table of all `/api/*` endpoints with example curl commands
- **Manage / import / export**: how to use the web UI and `curl` for each
- **Docker deployment**: `cp .env.example .env`, set `DOMAIN`, `docker compose up -d`
- **Release / upgrade**: `git tag v1.x.x && git push origin v1.x.x`, then `docker compose pull && docker compose up -d` on the server
- **Development**: `uv sync`, pre-commit install, running tests, CI badges

### `PLAN.md`

A copy of this planning document committed to the repo root. Serves as the implementation roadmap and architectural decision record — useful for onboarding and for Claude Code context in future sessions.

---

## GitHub Repository

Create a public repo under `ubahmapk` and push the initial commit:

```bash
gh repo create food-picker --public --source=. --remote=origin --description "Random food picker web app" --push
```

### MIT License

Create `LICENSE` in the project root:

```
MIT License

Copyright (c) 2026 Jon Mark Allen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### `.gitignore` additions needed

The existing `.gitignore` covers Python artifacts and `.venv`. Add:
```
# Tool caches
.pytest_cache/
.ruff_cache/
.cache/

# Runtime output
log*/

# Secrets / environment
.env

# Docker
caddy_data/
```

**Do NOT add** `tests/`, `.claude/`, or `CLAUDE.md` — all three should be committed.

`places.toml` should be committed as the initial seed data. Runtime edits via the app won't auto-commit, but the file can be updated in git manually when the canonical list changes.

---

## GitHub Actions CI

**File**: `.github/workflows/ci.yml`

Runs on every push and PR to `main`:
1. `uv sync`
2. `uv run ruff check --config=.ruff.toml`
3. `uv run ruff format --check --config=.ruff.toml`
4. `uv run ty check`
5. `uv run bandit -c .bandit.yml -r app/`
6. `uv run pytest` (with coverage; fails if <80%)

```yaml
name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.14"
      - run: uv sync
      - run: uv run ruff check --config=.ruff.toml
      - run: uv run ruff format --check --config=.ruff.toml
      - run: uv run ty check
      - run: uv run bandit -c .bandit.yml -r app/
      - run: uv run pytest
```

---

## GitHub Actions: Release Automation

**File**: `.github/workflows/release.yml`

Triggers on pushed tags matching `v*.*.*`. Builds and pushes a Docker image to GitHub Container Registry (GHCR), tagged with both the semver tag and `latest`.

```yaml
name: Release
on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=raw,value=latest

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

**Release workflow:**
1. CI must be green on `main`
2. Tag the commit: `git tag v1.0.0 && git push origin v1.0.0`
3. The release workflow builds the Docker image, pushes to `ghcr.io/ubahmapk/food-picker:1.0.0` and `:latest`, and creates a GitHub Release with auto-generated notes
4. On the server: `docker compose pull && docker compose up -d` to deploy the new image (update `docker-compose.yml` to use the GHCR image tag instead of building locally for production)

---

## Dependabot

**File**: `.github/dependabot.yml`

Auto-opens PRs to bump GitHub Actions and `uv`/pip dependencies weekly:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## CLAUDE.md

Committed to the project root. Documents key commands for Claude Code so it can assist effectively without re-discovering them:

```markdown
# food-picker

## Commands
- `uv sync` — install all dependencies
- `uv run flask --app app run --debug` — dev server (set PLACES_FILE=./places.toml)
- `uv run pytest` — run tests with coverage
- `uv run ruff check --config=.ruff.toml` — lint
- `uv run ty check` — typecheck
- `uv run bandit -c .bandit.yml -r app/` — security scan
- `uv run pre-commit run --all-files` — run all pre-commit hooks

## Architecture
API-first Flask app. All business logic is in `/api/` blueprint (JSON responses via orjson).
The SPA at `/static/index.html` calls the API. Data is stored in `places.toml` (atomic writes).
```

---

## Verification

### Local dev
```bash
uv sync
# Seed places.toml from choices.md (one-time)
uv run python -m app.seed
# Run dev server
PLACES_FILE=./places.toml uv run flask --app app run --debug
```

**Run tests with coverage:**
```bash
uv run pytest
```
Confirm ≥80% branch coverage reported; all tests pass before proceeding to Docker/prod testing.

**API tests via curl:**
```bash
curl http://localhost:5000/api/categories
curl "http://localhost:5000/api/pick"
curl "http://localhost:5000/api/pick?categories=Fast+Food"
curl "http://localhost:5000/api/pick?categories=Fast+Food&vetoed=McDonalds"
curl -X POST http://localhost:5000/api/places \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Place", "categories": ["Fast Food"]}'
curl http://localhost:5000/api/export?format=toml
curl http://localhost:5000/api/export?format=json
```

**Web frontend tests:**
- Open `http://localhost:5000` in a mobile browser or DevTools mobile emulation
- Category toggles work; "Pick for me" returns a result
- Veto accumulates correctly (same place never repeats in one session)
- Manage view: add/edit/delete places and categories; verify `places.toml` updates on disk
- Import: export a TOML, edit it, re-import; verify changes appear

### Docker (no real domain)
- Temporarily expose port 8000 on app service
- `docker compose up app`; repeat curl and browser tests

### Production
- DNS A record for `eat.starfleet.top` → host IP, ports 80/443 open
- `DOMAIN=eat.starfleet.top` in `.env` (default); `docker compose up -d`
- Verify HTTPS + valid LE cert at `https://eat.starfleet.top`; HTTP redirects to HTTPS
- To run on a different hostname: change `DOMAIN` in `.env` and redeploy
