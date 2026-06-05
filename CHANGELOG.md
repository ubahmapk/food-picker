# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Claude Code memory rule: update `PLAN.md` after architectural and design decisions to keep the design record current across sessions
- Claude Code hooks refactored: removed hardcoded project path (portable across workstations), split monolithic command into four separate hooks — one per file type (Python, TOML, YAML, docker-compose) — each with a guard clause for readability and maintainability
- API-first Flask app: all business logic in `/api/*` JSON endpoints (curl-friendly)
- `GET /api/pick` with optional `?categories=` filter and stateless `?vetoed=` accumulation; uses `secrets.choice()` to avoid PRNG bias
- Full CRUD for places: `GET/POST /api/places`, `DELETE/PUT /api/places/<name>` (name and categories updatable independently)
- Full CRUD for categories: `GET/POST /api/categories`, `DELETE /api/categories/<name>`, `PUT /api/categories` (reorder)
- TOML and JSON import/export endpoints (`GET /api/export?format=toml|json`, `POST /api/import`)
- Pydantic v2 data validation for all API inputs; atomic TOML writes via `Path.replace()`
- Vanilla JS SPA frontend with Pico CSS v2; no build step, no framework
- Mobile-optimized home view: category checkboxes, Pick for Me / Veto - Pick Again / That's It! flow
- Veto list displayed below the result card showing all places vetoed in the current session; cleared on accept
- Theme toggle button (🌓 auto / ☀️ light / 🌙 dark) in the nav bar; preference persisted to `localStorage`; FOUC-prevention inline `<script>` applies saved theme before CSS loads
- Inline place editing in Manage view: expand a card to edit name and categories in place; calls existing `PUT /api/places/<name>` endpoint
- `escHtml()` helper applied to all user-supplied strings rendered into `innerHTML`
- Tabbed Manage view (Places / Categories / Import+Export) using Pico CSS `role="group"` tab bar
- Category deletion UI in the Categories tab, backed by existing `DELETE /api/categories/<name>` API
- Pico CSS semantic CSS variables throughout (`--pico-muted-border-color`, `--pico-muted-background`, `--pico-color`) for automatic dark/light mode adaptation
- Caddy reverse proxy with auto Let's Encrypt TLS; domain configured via `{$DOMAIN}` env var
- Gunicorn multi-worker WSGI server (2 workers, port 8000)
- Docker Compose deployment with `caddy_data` named volume for certificate persistence across restarts
- GitHub Actions CI: ruff lint/format check, ty typecheck, bandit SAST, pytest with ≥80% branch coverage requirement
- GitHub Actions release automation: builds and pushes Docker image to GHCR + creates GitHub Release on `v*.*.*` tags
- Dependabot: weekly GitHub Actions and pip dependency bump PRs
- Pre-commit hooks: trailing whitespace, YAML validation, ruff format/check, bandit
- Claude Code PostToolUse hooks: auto-format, lint, typecheck, and security scan on file save
- One-time `app/seed.py` migration script to convert `choices.md` → `places.toml`
- MIT License

### Fixed

- Local dev server switched from port 5000 to 8000 to avoid macOS AirPlay Receiver (ControlCenter) conflict
- Category tag chips updated to `--pico-muted-background` + `--pico-color` for readable contrast in both light and dark modes (previously `--pico-secondary` was unreadably low-contrast in light mode)

[Unreleased]: https://github.com/ubahmapk/food-picker/commits/main/
