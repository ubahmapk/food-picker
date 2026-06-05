import os
import tempfile
from pathlib import Path

import pytest

from app import create_app
from app.data import save_places
from app.models import Place, PlacesData


@pytest.fixture
def tmp_places_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        tmp_path = f.name

    yield tmp_path

    if Path(tmp_path).exists():
        Path(tmp_path).unlink()


@pytest.fixture
def app(tmp_places_file):
    os.environ["PLACES_FILE"] = tmp_places_file

    data = PlacesData(
        categories=["Fast Food", "Quality Nommings"],
        places=[
            Place(name="McDonalds", categories=["Fast Food"]),
            Place(name="Whataburger", categories=["Fast Food"]),
            Place(name="Five Guys", categories=["Fast Food", "Quality Nommings"]),
            Place(name="Rosa's Cafe", categories=["Quality Nommings"]),
        ],
    )

    save_places(tmp_places_file, data)

    app_instance = create_app()
    app_instance.config["TESTING"] = True

    yield app_instance


@pytest.fixture
def client(app):
    return app.test_client()
