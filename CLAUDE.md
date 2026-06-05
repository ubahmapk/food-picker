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

Design decisions have been documented in `PLAN.md` and serve as a sort-of record of why certain decisions were made and can re-establish the full design context cleanly.

## Release process

1. Update `CHANGELOG.md`: move `[Unreleased]` → `[x.y.z] - YYYY-MM-DD`, add fresh empty `[Unreleased]` above, update comparison link at bottom
2. `git add CHANGELOG.md && git commit -m "chore: release vx.y.z"`
3. `git tag vx.y.z && git push origin vx.y.z`
4. CI builds the Docker image → pushes to GHCR → creates GitHub Release automatically

Semver: new feature = minor bump, bug fix = patch, breaking API change = major.
