import json
import os
from pathlib import Path

import orjson
import tomli_w
import tomllib

from app.models import Place, PlacesData


def get_places_file() -> str:
    return os.getenv("PLACES_FILE", "/app/places.toml")


def load_places(path: str) -> PlacesData:
    path_obj = Path(path)

    if not path_obj.exists():
        migrate_from_choices_md(Path(path).parent / "choices.md", path)

    with Path(path).open("rb") as f:
        data = tomllib.load(f)

    return PlacesData.model_validate(data)


def save_places(path: str, data: PlacesData) -> None:
    tmp_path = Path(f"{path}.tmp")
    content = tomli_w.dumps(data.model_dump())

    with tmp_path.open("w") as f:
        f.write(content)

    tmp_path.replace(path)


def migrate_from_choices_md(md_path: Path, toml_path: str) -> None:
    if not md_path.exists():
        default_data = PlacesData(categories=[], places=[])
        save_places(toml_path, default_data)
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

    categories = list(categories_dict.keys())
    places = [
        Place(name=name, categories=[cat])
        for cat, names in categories_dict.items()
        for name in names
    ]

    data = PlacesData(categories=categories, places=places)
    save_places(toml_path, data)


def export_toml(data: PlacesData) -> bytes:
    return tomli_w.dumps(data.model_dump()).encode("utf-8")


def export_json(data: PlacesData) -> bytes:
    return orjson.dumps(data.model_dump(), option=orjson.OPT_INDENT_2)


def import_data(raw: bytes, fmt: str) -> PlacesData:
    if fmt == "json":
        parsed = json.loads(raw)
    elif fmt == "toml":
        parsed = tomllib.loads(raw.decode("utf-8"))
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    return PlacesData.model_validate(parsed)
