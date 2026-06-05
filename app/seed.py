"""One-time migration: convert choices.md to places.toml."""

import os
from pathlib import Path

import tomli_w
from pydantic import BaseModel


class _Place(BaseModel):
    name: str
    categories: list[str]


class _PlacesData(BaseModel):
    categories: list[str]
    places: list[_Place]


def run(md_path: Path, toml_path: Path) -> None:
    if toml_path.exists():
        print(f"{toml_path} already exists — skipping migration.")
        return

    if not md_path.exists():
        print(f"{md_path} not found — creating empty places.toml.")
        data = _PlacesData(categories=[], places=[])
        _write(toml_path, data)
        return

    categories_dict: dict[str, list[str]] = {}
    current_category = None

    with md_path.open() as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_category = line[3:].strip()
                categories_dict[current_category] = []
            elif line.startswith("- ") and current_category:
                place_name = line[2:].strip()
                if place_name:
                    categories_dict[current_category].append(place_name)

    data = _PlacesData(
        categories=list(categories_dict.keys()),
        places=[
            _Place(name=name, categories=[cat])
            for cat, names in categories_dict.items()
            for name in names
        ],
    )

    _write(toml_path, data)
    print(
        f"Migrated {sum(len(v) for v in categories_dict.values())} places "
        f"across {len(data.categories)} categories to {toml_path}."
    )


def _write(path: Path, data: _PlacesData) -> None:
    tmp = Path(f"{path}.tmp")
    tmp.write_text(tomli_w.dumps(data.model_dump()))
    tmp.replace(path)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    choices = project_root / "choices.md"
    places = Path(os.getenv("PLACES_FILE", str(project_root / "places.toml")))
    run(choices, places)
