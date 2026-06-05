# Food Picker

A fast, lightweight web app to randomly select a restaurant from curated lists. Perfect for family meal decisions.

**Live at**: [eat.starfleet.top](https://eat.starfleet.top)

## Quick Start

### Local Development

```bash
uv sync
uv run python -m app.seed  # one-time: migrate choices.md to places.toml
PLACES_FILE=./places.toml uv run flask --app app run --debug --port 8000
```

Visit `http://localhost:8000`.

> **macOS note**: Port 5000 is used by AirPlay Receiver (ControlCenter) and redirects to HTTPS. Always use `--port 8000` for local dev.

### Docker

```bash
cp .env.example .env
# Edit .env if you want to change the domain (default: eat.starfleet.top)
docker compose up -d
```

Then visit `https://eat.starfleet.top` (or your configured domain).

## API Reference

All endpoints return JSON. Use `curl` directly if you prefer.

### Pick a restaurant

```bash
curl "https://eat.starfleet.top/api/pick"
curl "https://eat.starfleet.top/api/pick?categories=Fast+Food"
curl "https://eat.starfleet.top/api/pick?categories=Fast+Food&vetoed=McDonalds&vetoed=Wendy's"
```

Response: `{"name": "Whataburger"}` or `{"error": "no options remaining"}` (HTTP 409)

### Manage places

```bash
# List all places
curl https://eat.starfleet.top/api/places

# Add a place
curl -X POST https://eat.starfleet.top/api/places \
  -H "Content-Type: application/json" \
  -d '{"name": "Taco Bell", "categories": ["Fast Food"]}'

# Delete a place
curl -X DELETE "https://eat.starfleet.top/api/places/Taco%20Bell"

# Update a place
curl -X PUT "https://eat.starfleet.top/api/places/McDonalds" \
  -H "Content-Type: application/json" \
  -d '{"categories": ["Fast Food", "Quality Nommings"]}'
```

### Manage categories

```bash
# List all categories
curl https://eat.starfleet.top/api/categories

# Add a category
curl -X POST https://eat.starfleet.top/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name": "Fancy Fixings"}'

# Delete a category (removes it from all places)
curl -X DELETE "https://eat.starfleet.top/api/categories/Fancy%20Fixings"

# Reorder categories
curl -X PUT https://eat.starfleet.top/api/categories \
  -H "Content-Type: application/json" \
  -d '{"categories": ["Quality Nommings", "Fast Food", "Fancy Fixings"]}'
```

### Import / Export

```bash
# Export as TOML
curl https://eat.starfleet.top/api/export?format=toml > places.toml

# Export as JSON
curl https://eat.starfleet.top/api/export?format=json > places.json

# Import from TOML or JSON
curl -X POST https://eat.starfleet.top/api/import \
  -F "file=@places.toml"
```

## Web UI

- **Home** → Select categories, pick a restaurant, veto for another, or accept
- **Manage** → Add/delete places and categories, import/export data

Mobile-optimized via Pico CSS.

## Development

```bash
# Run tests with coverage (min 80%)
uv run pytest

# Format and lint
uv run ruff format --config=.ruff.toml
uv run ruff check --fix --config=.ruff.toml

# Typecheck
uv run ty check

# Security scan
uv run bandit -c .bandit.yml -r app/

# Pre-commit hooks (installed via uv run pre-commit install)
uv run pre-commit run --all-files
```

## Deployment

### Release a new version

```bash
git tag v1.0.0
git push origin v1.0.0
```

The CI will build and push the Docker image to `ghcr.io/ubahmapk/food-picker:1.0.0` and `:latest`.

### Deploy on the server

```bash
docker compose pull
docker compose up -d
```

## Architecture

- **Backend**: Flask API (Python 3.14 + Pydantic)
- **Frontend**: Vanilla JS SPA (no build step, no frameworks)
- **Data**: TOML file (atomic writes for safety)
- **Reverse proxy**: Caddy (auto Let's Encrypt HTTPS)
- **WSGI**: Gunicorn (2 workers)

See `PLAN.md` for detailed design decisions and full specification.

## License

MIT © 2026 Jon Mark Allen
