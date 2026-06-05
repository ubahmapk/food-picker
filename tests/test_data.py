import os
import tempfile
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data import (
    export_json,
    export_toml,
    get_places_file,
    import_data,
    load_places,
    migrate_from_choices_md,
    save_places,
)
from app.models import Place, PlacesData


def test_load_and_save_places(tmp_places_file):
    data = PlacesData(
        categories=["Test"],
        places=[Place(name="Test Place", categories=["Test"])],
    )

    save_places(tmp_places_file, data)
    loaded = load_places(tmp_places_file)

    assert loaded.categories == ["Test"]
    assert len(loaded.places) == 1
    assert loaded.places[0].name == "Test Place"


def test_save_places_atomic(tmp_places_file):
    data = PlacesData(
        categories=["Cat1"],
        places=[Place(name="Place1", categories=["Cat1"])],
    )

    save_places(tmp_places_file, data)

    with open(tmp_places_file, "rb") as f:
        content = tomllib.load(f)

    assert content["categories"] == ["Cat1"]
    assert len(content["places"]) == 1


def test_load_places_auto_migrates(tmp_places_file):
    """load_places migrates choices.md when places.toml doesn't exist."""
    Path(tmp_places_file).unlink()

    md_content = "# Restaurants\n\n## Fast Food\n\n- McDonalds\n- Wendy's\n"
    md_path = tmp_places_file.replace(".toml", "_choices.md")
    with open(md_path, "w") as f:
        f.write(md_content)

    os.environ["PLACES_FILE"] = tmp_places_file

    data = migrate_from_choices_md(Path(md_path), tmp_places_file)

    assert Path(tmp_places_file).exists()

    loaded = load_places(tmp_places_file)
    assert "Fast Food" in loaded.categories
    assert any(p.name == "McDonalds" for p in loaded.places)

    Path(md_path).unlink()


def test_migrate_no_choices_md(tmp_places_file):
    """migrate_from_choices_md creates an empty data file when choices.md is absent."""
    Path(tmp_places_file).unlink()
    migrate_from_choices_md(Path("/nonexistent/choices.md"), tmp_places_file)
    loaded = load_places(tmp_places_file)
    assert loaded.categories == []
    assert loaded.places == []


def test_get_places_file_from_env():
    os.environ["PLACES_FILE"] = "/tmp/test.toml"
    assert get_places_file() == "/tmp/test.toml"


def test_export_json():
    data = PlacesData(
        categories=["Test"],
        places=[Place(name="Test", categories=["Test"])],
    )

    exported = export_json(data)
    assert isinstance(exported, bytes)
    assert b"Test" in exported


def test_export_toml():
    data = PlacesData(
        categories=["Test"],
        places=[Place(name="Test", categories=["Test"])],
    )

    exported = export_toml(data)
    assert isinstance(exported, bytes)
    assert b"Test" in exported


def test_import_json():
    json_data = b'{"categories": ["Cat1"], "places": [{"name": "Place1", "categories": ["Cat1"]}]}'

    result = import_data(json_data, "json")

    assert result.categories == ["Cat1"]
    assert result.places[0].name == "Place1"


def test_import_toml():
    toml_data = b'categories = ["Cat1"]\n\n[[places]]\nname = "Place1"\ncategories = ["Cat1"]'

    result = import_data(toml_data, "toml")

    assert result.categories == ["Cat1"]
    assert result.places[0].name == "Place1"


def test_import_unsupported_format():
    with pytest.raises(ValueError, match="Unsupported format"):
        import_data(b"data", "xml")


def test_import_invalid_json():
    invalid_json = b'{"invalid": json}'

    with pytest.raises(Exception):
        import_data(invalid_json, "json")


def test_load_places_auto_creates_when_missing(tmp_places_file):
    """load_places auto-creates an empty places.toml if the file doesn't exist."""
    Path(tmp_places_file).unlink()
    loaded = load_places(tmp_places_file)
    assert loaded.categories == []
    assert loaded.places == []
    assert Path(tmp_places_file).exists()


def test_place_validation_empty_name():
    with pytest.raises(ValidationError):
        Place(name="", categories=["Test"])


def test_place_validation_empty_categories():
    with pytest.raises(ValidationError):
        Place(name="Test", categories=[])
