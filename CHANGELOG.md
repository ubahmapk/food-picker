# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-05

### Added

- About page accessible from the nav bar; fetches app info from `GET /api/about`
- `GET /api/about` endpoint returning app name, description, repo URL, and tech stack
- `PUT /api/categories/<name>` endpoint to rename a category; rename cascades to all places that use it
- Inline category rename in the Manage → Categories tab (same Edit/Save/Cancel pattern as place editing)
- "Add Place" and "Add Category" forms moved to the top of their respective Manage tabs, above the list of existing items
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

- `load_places()` now returns an empty `PlacesData` (categories=[], places=[]) instead of raising a 500 when `places.toml` is missing or contains malformed TOML or invalid data structure
- Logo/header `🍽️ Food Picker` is now a hyperlink that navigates back to the home (Pick) view
- Claude Code memory rule: update `PLAN.md` after architectural and design decisions to keep the design record current across sessions
- Claude Code hooks refactored: removed hardcoded project path (portable across workstations), split monolithic command into four separate hooks — one per file type (Python, TOML, YAML, docker-compose) — each with a guard clause for readability and maintainability
- Local dev server switched from port 5000 to 8000 to avoid macOS AirPlay Receiver (ControlCenter) conflict
- Category tag chips updated to `--pico-muted-background` + `--pico-color` for readable contrast in both light and dark modes (previously `--pico-secondary` was unreadably low-contrast in light mode)
- DOM-based XSS vulnerabilities in app.js: replaced all unescaped innerHTML string interpolations with escaped text nodes or addEventListener-based event handling
- SRI integrity attribute added to Pico CSS CDN link in index.html to prevent supply-chain tampering
- Docker image now runs as non-root user (appuser, UID 1001) per container security best practices

[Unreleased]: https://github.com/ubahmapk/food-picker/compare/v0.1.0...main
[0.1.0]: https://github.com/ubahmapk/food-picker/releases/tag/v0.1.0
