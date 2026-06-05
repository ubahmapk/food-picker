# food-picker

## Commands

- `uv sync` — install all dependencies
- `PLACES_FILE=./places.toml uv run flask --app app run --debug --port 8000` — dev server (port 8000 avoids macOS AirPlay on 5000)
- `uv run pytest` — run tests with coverage
- `uv run ruff check --config=.ruff.toml` — lint
- `uv run ty check` — typecheck
- `uv run bandit -c .bandit.yml -r app/` — security scan
- `uv run pre-commit run --all-files` — run all pre-commit hooks

## Architecture

API-first Flask app. All business logic is in `/api/` blueprint (JSON responses via orjson).
The SPA at `/static/index.html` calls the API. Data is stored in `places.toml` (atomic writes).
